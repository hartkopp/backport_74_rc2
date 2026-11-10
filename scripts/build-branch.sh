#!/bin/bash
# SPDX-License-Identifier: GPL-2.0
#
# Apply the backport series for one stable branch on top of a fresh test
# branch in a local linux-stable tree and build it with the minimal config
# from configs/.
#
# Usage: scripts/build-branch.sh [-e] [-b <base-ref>] <linux-tree> <X.Y>
#
#   -e             build after each patch of the series (bisectability),
#                  default: build once after the complete series
#   -b <base-ref>  base of the test branch, default: origin/linux-X.Y.y
#   <linux-tree>   path to the local linux-stable git tree
#   <X.Y>          stable version, e.g. 5.10 or 6.18
#
# Environment (defaults in brackets):
#   OBJ     build output directory [/ramdisk]
#   JOBS    parallel make jobs     [16]
#   CC_CMD  compiler               ["ccache gcc"]
#
# The test branch bp-test/X.Y is (re)created with 'git checkout -B'.
# Patches from linux-X.Y.y/queued/ are skipped when the base already
# contains them (lookup of the upstream commit id in the commit messages).

set -e

each=0
base=
while getopts "eb:" opt; do
	case $opt in
	e) each=1 ;;
	b) base=$OPTARG ;;
	*) sed -n '4,22p' "$0"; exit 1 ;;
	esac
done
shift $((OPTIND - 1))

if [ $# -ne 2 ]; then
	sed -n '4,22p' "$0"
	exit 1
fi

tree=$1
ver=$2
repo=$(cd "$(dirname "$0")/.." && pwd)
dir=$repo/linux-$ver.y
cfg=$repo/configs/linux-$ver.y.config
base=${base:-origin/linux-$ver.y}
OBJ=${OBJ:-/ramdisk}
JOBS=${JOBS:-16}
CC_CMD=${CC_CMD:-ccache gcc}

[ -d "$dir" ] || { echo "no patch directory $dir"; exit 1; }
[ -f "$cfg" ] || { echo "no config $cfg"; exit 1; }
[ -d "$OBJ" ] || { echo "no build directory $OBJ"; exit 1; }

build() {
	echo "### build: $(git log -1 --format='%h %s')"
	cp "$cfg" "$OBJ/.config"
	make -s O="$OBJ" olddefconfig
	KBUILD_BUILD_TIMESTAMP='' make O="$OBJ" CC="$CC_CMD" -j"$JOBS"
}

cd "$tree"

# clean up a 'git am' left over from an interrupted run of this script,
# but never touch an 'am' session outside of the bp-test/* branches
if [ -d "$(git rev-parse --git-path rebase-apply)" ]; then
	case $(git symbolic-ref -q --short HEAD) in
	bp-test/*)
		echo "### aborting leftover 'git am' on $(git symbolic-ref -q --short HEAD)"
		git am --abort
		;;
	*)
		echo "'git am' in progress outside of bp-test/*, aborting"
		exit 1
		;;
	esac
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
	echo "$tree has uncommitted changes, aborting"
	exit 1
fi

echo "### base: $base ($(git log -1 --format='%h %s' "$base"))"
git checkout -q -B "bp-test/$ver" "$base"

# already queued patches: apply unless they landed in the base already
for p in "$dir"/queued/*.patch; do
	[ -e "$p" ] || continue
	up=$(grep -m1 -o -E '^commit [0-9a-f]{40} upstream' "$p" | cut -d' ' -f2 ||
	     true)
	[ -n "$up" ] || up=$(grep -m1 -o -E 'Upstream commit [0-9a-f]{40}' "$p" |
			     cut -d' ' -f3 || true)
	[ -n "$up" ] || up=$(grep -m1 -o -E 'cherry picked from commit [0-9a-f]{40}' "$p" |
			     cut -d' ' -f5 || true)
	if [ -n "$up" ] && git log --format=%H -1 --grep="$up" "$base" |
			   grep -q .; then
		echo "### skip (already in base): $(basename "$p")"
		continue
	fi
	echo "### queued: $(basename "$p")"
	git am -q --3way "$p"
done

if [ $each -eq 1 ]; then
	for p in "$dir"/0*.patch; do
		echo "### apply: $(basename "$p")"
		git am -q --3way "$p"
		build
	done
else
	for p in "$dir"/0*.patch; do
		echo "### apply: $(basename "$p")"
	done
	git am -q --3way "$dir"/0*.patch
	build
fi

echo "### OK: linux-$ver.y ($(git log --oneline "$base"..HEAD | wc -l) commits on $base)"
