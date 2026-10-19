#!/usr/bin/env python3
"""Reconcile susfs4ksu's kernel-side patch with the GKI sublevel being built.

usage: susfs_patch_surgery.py <patch> <tree-root> <file:hunk> [<file:hunk> ...]

Each <file:hunk> is a hunk `patch --dry-run` rejected. A rejected hunk is
dropped from the patch and its addition re-inserted into the tree with an
anchor that exists on every android16-6.12 release. Hunks are recognised by
the content they add, never by @@ line numbers: susfs rebases the patch onto
one sublevel at a time, which renumbers every hunk in the file.
"""
import io
import re
import sys


def split_patch(text):
    """-> [(header_lines, path, [hunk_lines, ...]), ...]"""
    out, pre, path, hunks, cur = [], [], None, [], None

    def flush():
        if path is not None:
            if cur:
                hunks.append(cur)
            out.append([pre, path, hunks])

    for line in text.split('\n'):
        if line.startswith('diff --git '):
            flush()
            pre, path, hunks, cur = [line], None, [], None
        elif line.startswith('+++ b/') and path is None:
            path = line[6:]
            pre.append(line)
        elif line.startswith('@@'):
            if cur:
                hunks.append(cur)
            cur = [line]
        elif cur is not None:
            cur.append(line)
        else:
            pre.append(line)
    flush()
    return out


def join_patch(sections):
    chunks = []
    for pre, _path, hunks in sections:
        chunks.append('\n'.join(pre))
        for h in hunks:
            chunks.append('\n'.join(h))
    return '\n'.join(chunks)


def added(hunk):
    return '\n'.join(l[1:] for l in hunk if l.startswith('+'))


GUARD_MAP = '#ifdef CONFIG_KSU_SUSFS_SUS_MAP'
ENDIF_MAP = '#endif // #ifdef CONFIG_KSU_SUSFS_SUS_MAP'


def insert_exec_include(tree):
    """fs/exec.c: the susfs_def.h include. Context differs because .23/.38
    have no <linux/dma-buf.h>; <linux/ksm.h> is on every release."""
    path = tree + '/fs/exec.c'
    s = io.open(path, encoding='utf-8').read()
    if 'susfs_def.h' in s:
        return 'already present'
    anchor = '#include <linux/ksm.h>\n'
    if s.count(anchor) != 1:
        return None
    block = anchor + '#ifdef CONFIG_KSU_SUSFS\n#include <linux/susfs_def.h>\n#endif\n'
    io.open(path, 'w', encoding='utf-8').write(s.replace(anchor, block, 1))
    return 'inserted after <linux/ksm.h>'


def insert_show_smap_guard(tree):
    """task_mmu.c show_smap(): vma_pages() was renamed vma_data_pages() in
    6.12.69, and .92 added a priv local, so match either spelling."""
    path = tree + '/fs/proc/task_mmu.c'
    s = io.open(path, encoding='utf-8').read()
    if 'SUSFS_IS_INODE_SUS_MAP' in s and 'return 0;\n\t}\n#endif' in s:
        return 'already present'
    m = re.search(r'^\tif \(!vma_(?:data_)?pages\(vma\)\)$', s, re.M)
    if not m or len(re.findall(r'^\tif \(!vma_(?:data_)?pages\(vma\)\)$', s, re.M)) != 1:
        return None
    block = (GUARD_MAP + '\n'
             '\tif (vma->vm_file) {\n'
             '\t\tif (SUSFS_IS_INODE_SUS_MAP(file_inode(vma->vm_file)))\n'
             '\t\t\treturn 0;\n'
             '\t}\n'
             + ENDIF_MAP + '\n\n')
    io.open(path, 'w', encoding='utf-8').write(s[:m.start()] + block + s[m.start():])
    return 'inserted before vma_pages() check'


def insert_rollup_bypass(tree):
    """task_mmu.c show_smaps_rollup(): .92 rewrote the locking and iteration
    (lock_vma_range/nr_contended), so the upstream anchors do not exist on
    older releases. There the equivalent spot is the head of the do-loop:
    skip the gather for a sus-mapped VMA but still advance last_vma_end."""
    path = tree + '/fs/proc/task_mmu.c'
    s = io.open(path, encoding='utf-8').read()
    if 'bypass_orig_flow' in s:
        return 'already present'
    anchor = ('\tvma_start = vma->vm_start;\n'
              '\tdo {\n'
              '\t\tsmap_gather_stats(vma, &mss, 0);\n'
              '\t\tlast_vma_end = vma->vm_end;\n')
    if s.count(anchor) != 1:
        return None
    block = ('\tvma_start = vma->vm_start;\n'
             '\tdo {\n'
             + GUARD_MAP + '\n'
             '\t\tif (vma->vm_file && SUSFS_IS_INODE_SUS_MAP(file_inode(vma->vm_file)))\n'
             '\t\t\tgoto bypass_orig_flow;\n'
             + ENDIF_MAP + '\n'
             '\t\tsmap_gather_stats(vma, &mss, 0);\n'
             + GUARD_MAP + '\n'
             'bypass_orig_flow:\n'
             + ENDIF_MAP + '\n'
             '\t\tlast_vma_end = vma->vm_end;\n')
    io.open(path, 'w', encoding='utf-8').write(s.replace(anchor, block, 1))
    return 'inserted at show_smaps_rollup() loop head'


# (target file, marker in the hunk's added lines) -> re-inserter. Several
# markers share one inserter where upstream splits an edit across hunks.
RULES = [
    ('fs/exec.c', '#include <linux/susfs_def.h>', insert_exec_include),
    ('fs/proc/task_mmu.c', 'SUSFS_IS_INODE_SUS_MAP(file_inode(vma->vm_file)))\n\t\t\treturn 0;', insert_show_smap_guard),
    ('fs/proc/task_mmu.c', 'goto bypass_orig_flow;', insert_rollup_bypass),
    ('fs/proc/task_mmu.c', 'bypass_orig_flow:', insert_rollup_bypass),
]


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    patch_path, tree = sys.argv[1], sys.argv[2].rstrip('/')
    wanted = set()
    for spec in sys.argv[3:]:
        f, _, n = spec.rpartition(':')
        wanted.add((f, int(n)))

    sections = split_patch(io.open(patch_path, encoding='utf-8').read())
    done, failed = [], []

    for sec in sections:
        _pre, path, hunks = sec
        keep = []
        for idx, hunk in enumerate(hunks, 1):
            if (path, idx) not in wanted:
                keep.append(hunk)
                continue
            body = added(hunk)
            fn = next((f for p, marker, f in RULES if p == path and marker in body), None)
            if fn is None:
                failed.append('%s hunk #%d: no re-insertion rule for this content' % (path, idx))
                keep.append(hunk)
                continue
            note = fn(tree)
            if note is None:
                failed.append('%s hunk #%d: anchor not found in tree' % (path, idx))
                keep.append(hunk)
                continue
            done.append('%s hunk #%d -> %s' % (path, idx, note))
        sec[2] = keep

    for line in done:
        print('   reconciled: ' + line)
    for line in failed:
        print('   UNRESOLVED: ' + line)

    if failed:
        return 1

    io.open(patch_path, 'w', encoding='utf-8').write(join_patch(sections))
    return 0


if __name__ == '__main__':
    sys.exit(main())
