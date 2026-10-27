\version "2.24.0"
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
\include "winter1.ly"
\include "winter1a.ly"
\include "winter1b.ly"
\include "winter1c.ly"
\include "winter1d.ly"
\include "winter2.ly"
\include "winter2a.ly"
\include "winter2b.ly"
\include "winter2c.ly"
\include "winter2d.ly"
\include "winter3.ly"
\include "winter3a.ly"
\include "winter3b.ly"
\include "winter3c.ly"
\include "winter3d.ly"
\score { << \new Staff = "1-solo" { \ViolinoPrincipaleWinterOne }
\new Staff = "1-violin1" { \ViolinoPrimoWinterOne }
\new Staff = "1-violin2" { \ViolinoSecondoWinterOne }
\new Staff = "1-viola" { \AltoViolaWinterOne }
\new Staff = "1-cello" { \VioloncelloWinterOne } >> \layout { \context { \Voice \consists #capture-engraver } } }
\score { << \new Staff = "2-solo" { \ViolinoPrincipaleWinterTwo }
\new Staff = "2-violin1" { \ViolinoPrimoWinterTwo }
\new Staff = "2-violin2" { \ViolinoSecondoWinterTwo }
\new Staff = "2-viola" { \AltoViolaWinterTwo }
\new Staff = "2-cello" { \VioloncelloWinterTwo } >> \layout { \context { \Voice \consists #capture-engraver } } }
\score { << \new Staff = "3-solo" { \ViolinoPrincipaleWinterThree }
\new Staff = "3-violin1" { \ViolinoPrimoWinterThree }
\new Staff = "3-violin2" { \ViolinoSecondoWinterThree }
\new Staff = "3-viola" { \AltoViolaWinterThree }
\new Staff = "3-cello" { \VioloncelloWinterThree } >> \layout { \context { \Voice \consists #capture-engraver } } }