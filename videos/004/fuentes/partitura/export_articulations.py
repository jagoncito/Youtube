from pathlib import Path
base=r'''\version "2.24.0"
#(define (staff-id context)
  (if (eq? 'Staff (ly:context-name context))
      (ly:context-id context)
      (let ((parent (ly:context-parent context)))
       (if parent (staff-id parent) "unknown"))))
#(define (capture-engraver context)
   (make-engraver
    (listeners
     ((note-event engraver event)
      (let* ((now (ly:context-current-moment context))
             (pitch (ly:event-property event 'pitch))
             (dur (ly:duration-length (ly:event-property event 'duration))))
         (format #t "NOTE~a|~a|~a|~a|~a|~a~%"
          (staff-id context)
          (ly:moment-main-numerator now)
          (ly:moment-main-denominator now)
          (+ 60 (ly:pitch-semitones pitch))
          (ly:moment-main-numerator dur)
          (ly:moment-main-denominator dur))))
     ((articulation-event engraver event)
      (let ((now (ly:context-current-moment context)))
        (format #t "ART~a|~a|~a|~s~%"
          (staff-id context)
          (ly:moment-main-numerator now)
          (ly:moment-main-denominator now)
          (ly:event-property event 'articulation-type))))
     ((slur-event engraver event)
      (let ((now (ly:context-current-moment context)))
        (format #t "SLUR~a|~a|~a|~s~%"
          (staff-id context)
          (ly:moment-main-numerator now)
          (ly:moment-main-denominator now)
          (ly:event-property event 'span-direction))))
     ((phrasing-slur-event engraver event)
      (let ((now (ly:context-current-moment context)))
        (format #t "PHRASE~a|~a|~a|~s~%"
          (staff-id context)
          (ly:moment-main-numerator now)
          (ly:moment-main-denominator now)
          (ly:event-property event 'span-direction))))
     ((tie-event engraver event)
      (let ((now (ly:context-current-moment context)))
        (format #t "TIE~a|~a|~a~%"
          (staff-id context)
          (ly:moment-main-numerator now)
          (ly:moment-main-denominator now)))))))
'''
incs=[];scores=[]
for number,word in [(1,'One'),(2,'Two'),(3,'Three')]:
 st=[]
 for suffix,var,track in [('', 'ViolinoPrincipale','solo'),('a','ViolinoPrimo','violin1'),('b','ViolinoSecondo','violin2'),('c','AltoViola','viola'),('d','Violoncello','cello')]:
  incs.append('\\include "winter%d%s.ly"'%(number,suffix))
  st.append('\\new Staff = "%d-%s" { \\%sWinter%s }'%(number,track,var,word))
 scores.append('\\score { << '+'\n'.join(st)+' >> \\layout { \\context { \\Voice \\consists #capture-engraver } } }')
Path('adapted/export-articulations.ly').write_text(base+'\n'.join(incs)+'\n'+'\n'.join(scores))
