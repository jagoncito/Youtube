\version "2.24.0"
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
\score { << \new Staff \new Voice = "1-solo" \with { \consists #capture-engraver } { \ViolinoPrincipaleWinterOne }
\new Staff \new Voice = "1-violin1" \with { \consists #capture-engraver } { \ViolinoPrimoWinterOne }
\new Staff \new Voice = "1-violin2" \with { \consists #capture-engraver } { \ViolinoSecondoWinterOne }
\new Staff \new Voice = "1-viola" \with { \consists #capture-engraver } { \AltoViolaWinterOne }
\new Staff \new Voice = "1-cello" \with { \consists #capture-engraver } { \VioloncelloWinterOne } >> \layout {} }
\score { << \new Staff \new Voice = "2-solo" \with { \consists #capture-engraver } { \ViolinoPrincipaleWinterTwo }
\new Staff \new Voice = "2-violin1" \with { \consists #capture-engraver } { \ViolinoPrimoWinterTwo }
\new Staff \new Voice = "2-violin2" \with { \consists #capture-engraver } { \ViolinoSecondoWinterTwo }
\new Staff \new Voice = "2-viola" \with { \consists #capture-engraver } { \AltoViolaWinterTwo }
\new Staff \new Voice = "2-cello" \with { \consists #capture-engraver } { \VioloncelloWinterTwo } >> \layout {} }
\score { << \new Staff \new Voice = "3-solo" \with { \consists #capture-engraver } { \ViolinoPrincipaleWinterThree }
\new Staff \new Voice = "3-violin1" \with { \consists #capture-engraver } { \ViolinoPrimoWinterThree }
\new Staff \new Voice = "3-violin2" \with { \consists #capture-engraver } { \ViolinoSecondoWinterThree }
\new Staff \new Voice = "3-viola" \with { \consists #capture-engraver } { \AltoViolaWinterThree }
\new Staff \new Voice = "3-cello" \with { \consists #capture-engraver } { \VioloncelloWinterThree } >> \layout {} }