#!/bin/zsh
# Learning curve: 24 topics in fixed order, two arms, rules on in both, Sonnet directing, draft quality.
#   ON : lessons the agent files after each reel are auto-accepted into this arm's home (an explicit
#        auto-accept regime, labelled as such) so later reels see earlier reels' lessons
#   OFF: lessons are filed but never accepted (inbox is inert) — each reel sees no lesson
# Both arms start from an empty lesson store. Quota stops are retried every 30 min.
R=~/.cache/reels-rsi-dev/venv/bin/reels; LOG=~/.reels/curve/curve.log; T=~/.reels/curve/topics.txt
for arm in ON OFF; do
  H=~/.cache/reels-curve-$arm; [ -d $H ] || { mkdir -p $H/lessons/{inbox,accepted,rejected} $H/rules; cp -r ~/.reels/fonts ~/.reels/sfx $H/; }
done
echo "=== curve start $(date)" | tee -a $LOG
i=0
while IFS='|' read -r genre topic; do
  i=$((i+1)); n=$(printf "%02d" $i)
  for arm in ON OFF; do
    export REELS_HOME=~/.cache/reels-curve-$arm
    D=~/.reels/curve/$arm/$n-$genre
    [ -f $D/renders/video.mp4 ] && continue
    case $genre in hist) style="ink or atlas (your choice)";; solve) style="chalk";; *) style="deepspace or notebook (your choice)";; esac
    for try in {1..12}; do
      echo "--- $arm $n $genre try $try $(date)" | tee -a $LOG
      rm -rf $D
      $R make "$topic" --dir $D --length 30 --quality draft --style "$style" --model sonnet --yes 2>&1 | tail -8 | tee -a $LOG
      if [ -f $D/renders/video.mp4 ]; then break; fi
      if grep -q "session limit\|usage limit\|rate limit" $LOG; then sleep 1800; else break; fi
    done
    if [ $arm = ON ]; then
      # auto-accept every doc/kit/taste lesson filed in this arm's inbox (rule lessons need a rule dir — left in the inbox)
      for f in $REELS_HOME/lessons/inbox/*.md; do [ -f "$f" ] || continue; grep -q '^kind: rule' "$f" && continue; $R lessons accept $(basename ${f%.md}) 2>&1 | tail -1 | tee -a $LOG; done
    fi
  done
done < $T
unset REELS_HOME
echo "=== curve end $(date)" | tee -a $LOG
