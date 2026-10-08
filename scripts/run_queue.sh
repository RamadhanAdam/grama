#!/bin/sh
# Runs experiment profiles one after another and keeps a status file.
#
#   sh scripts/run_queue.sh NAME profile1 profile2 ...
#
# results/queue_NAME.status gets one line per event (start, done, FAILED) with the UTC time, and
# results/queue_NAME.log gets what the runs print. A profile that fails (its data missing, for
# example) is logged and the queue goes on. Finished runs are kept in results/<profile>/runs.jsonl,
# so starting the same queue again resumes it where it stopped.
#
# Set PYTHON to use another interpreter. See `make paper1-background`, `make paper2-background`.

if [ "$#" -lt 2 ]; then
  echo "usage: sh scripts/run_queue.sh NAME profile [profile ...]" >&2
  exit 2
fi
NAME=$1
shift
PYTHON=${PYTHON:-python3}
cd "$(dirname "$0")/.." || exit 1
mkdir -p results
STATUS=results/queue_$NAME.status
LOG=results/queue_$NAME.log
PIDFILE=results/queue_$NAME.pid

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "Queue $NAME is already running (pid $(cat "$PIDFILE"))." >&2
  exit 1
fi
echo $$ > "$PIDFILE"

say() { echo "$(date -u '+%F %T') $*" >> "$STATUS"; }

say "queue $NAME started: $*"
for profile in "$@"; do
  say "start $profile"
  if "$PYTHON" scripts/run_experiments.py --profile "$profile" --no-progress >> "$LOG" 2>&1; then
    say "done $profile"
  else
    say "FAILED $profile (see $LOG)"
  fi
done
say "queue $NAME finished"
rm -f "$PIDFILE"
