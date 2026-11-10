#!/bin/bash
# SPDX-License-Identifier: GPL-2.0
#
# Run scripts/build-branch.sh for all stable branches and print a summary.
#
# Usage: scripts/build-all.sh [-e] <linux-tree> [<X.Y> ...]
#
#   -e            build after each patch of the series
#   <X.Y> ...     stable versions, default: 5.10 5.15 6.1 6.6 6.12 6.18
#
# The base of each test branch is origin/linux-X.Y.y. Build logs are
# written to build-X.Y.log in the current directory.

each=
if [ "$1" = "-e" ]; then
	each=-e
	shift
fi

if [ $# -lt 1 ]; then
	sed -n '4,12p' "$0"
	exit 1
fi

tree=$1
shift
versions=${*:-5.10 5.15 6.1 6.6 6.12 6.18}
script=$(cd "$(dirname "$0")" && pwd)/build-branch.sh
logdir=$(pwd)

declare -A result
for v in $versions; do
	echo "=== linux-$v.y (log: $logdir/build-$v.log)"
	if "$script" $each "$tree" "$v" > "$logdir/build-$v.log" 2>&1; then
		result[$v]=OK
	else
		result[$v]=FAILED
		# leave a clean tree for the next branch
		git -C "$tree" am --abort 2>/dev/null
	fi
	echo "    ${result[$v]}"
	grep -E 'warning:|error:' "$logdir/build-$v.log" | sed 's/^/    /' || true
done

echo
echo "=== summary"
for v in $versions; do
	printf '%-14s %s\n' "linux-$v.y" "${result[$v]}"
done
