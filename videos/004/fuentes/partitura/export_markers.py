from pathlib import Path
roots=Path('adapted')
base='''\\version "2.24.0"
#(define (capture-engraver context)
   (make-engraver
    (listeners
     ((text-script-event engraver event)
      (let* ((now (ly:context-current-moment context))
             (text (ly:event-property event 'text)))
         (format #t "MARKER~a|~a|~a|~s~%"
          (ly:context-id context)
          (ly:moment-main-numerator now)
          (ly:moment-main-denominator now)
          text))))))
'''
incs=[];scores=[]
for number,word in [(1,'One'),(2,'Two'),(3,'Three')]:
 st=[]
 for suffix,var,track in [('', 'ViolinoPrincipale','solo'),('a','ViolinoPrimo','violin1'),('b','ViolinoSecondo','violin2'),('c','AltoViola','viola'),('d','Violoncello','cello')]:
  incs.append('\\include "winter%d%s.ly"'%(number,suffix))
  st.append('\\new Staff \\new Voice = "%d-%s" \\with { \\consists #capture-engraver } { \\%sWinter%s }'%(number,track,var,word))
 scores.append('\\score { << '+'\n'.join(st)+' >> \\layout {} }')
(roots/'export-markers.ly').write_text(base+'\n'.join(incs)+'\n'+'\n'.join(scores))
