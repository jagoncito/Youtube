from pathlib import Path
import re,json
ROOT=Path(__file__).resolve().parent
source=(ROOT/'adapted/pathetique-2.ly').read_text()
preamble=source[:source.rindex('\\score {')]
scheme=r'''
#(define (parent-id context name)
 (if (eq? name (ly:context-name context))
  (ly:context-id context)
  (let ((parent (ly:context-parent context)))
   (if parent (parent-id parent name) "unknown"))))
#(define (head kind context)
 (let ((now (ly:context-current-moment context)))
  (format #t "EV|~a|~a|~a|~a|~a|~a|~a|~a"
   kind (parent-id context 'Staff) (parent-id context 'Voice)
   (ly:moment-main-numerator now) (ly:moment-main-denominator now)
   (ly:moment-grace-numerator now) (ly:moment-grace-denominator now)
   (ly:context-property context 'currentBarNumber))))
#(define (capture context)
 (make-engraver
  (listeners
   ((note-event engraver event)
    (let* ((pitch (ly:event-property event 'pitch))
           (dur (ly:duration-length (ly:event-property event 'duration))))
      (head "NOTE" context)
      (format #t "|~a|~a|~a~%" (+ 60 (ly:pitch-semitones pitch))
       (ly:moment-main-numerator dur) (ly:moment-main-denominator dur))))
   ((tie-event engraver event) (head "TIE" context) (format #t "~%"))
   ((articulation-event engraver event)
    (head "ART" context) (format #t "|~s~%" (ly:event-property event 'articulation-type)))
   ((slur-event engraver event)
    (head "SLUR" context) (format #t "|~a~%" (ly:event-property event 'span-direction)))
   ((phrasing-slur-event engraver event)
    (head "PHRASE" context) (format #t "|~a~%" (ly:event-property event 'span-direction)))
   ((absolute-dynamic-event engraver event)
    (head "DYNAMIC" context) (format #t "|~s~%" (ly:event-property event 'text)))
   ((crescendo-event engraver event)
    (head "CRESCENDO" context) (format #t "|~a|~s~%" (ly:event-property event 'span-direction) (ly:event-property event 'span-text)))
   ((decrescendo-event engraver event)
    (head "DECRESCENDO" context) (format #t "|~a|~s~%" (ly:event-property event 'span-direction) (ly:event-property event 'span-text)))
   ((sustain-event engraver event)
    (head "PEDAL" context) (format #t "|~a~%" (ly:event-property event 'span-direction)))
   ((tempo-change-event engraver event)
    (head "TEMPO" context) (format #t "|~s~%" (ly:event-property event 'text)))
   ((arpeggio-event engraver event)
    (head "ARPEGGIO" context) (format #t "~%"))
   ((text-script-event engraver event)
    (head "TEXT" context) (format #t "|~s~%" (ly:event-property event 'text)))
  )))
\score {
 \new PianoStaff <<
  \new Staff = "upper" <<
   \new Voice = "melody" { \voiceOne \topmain }
   \new Voice = "accompaniment" { \voiceTwo \topsecondary }
  >>
  \new Staff = "lower" { \bottom }
 >>
 \layout { \context { \Voice \consists #capture } }
}
'''
(ROOT/'adapted/export-events.ly').write_text(preamble+scheme)
