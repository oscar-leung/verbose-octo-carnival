import type { RubyToken } from '../../../shared/types';

/** Japanese text with optional furigana rendered as ruby annotations. */
export default function RubyText({ tokens, furigana }: { tokens: RubyToken[]; furigana: boolean }) {
  return (
    <span className={furigana ? 'ruby-text' : 'ruby-text no-furigana'}>
      {tokens.map((tok, i) =>
        tok.r ? (
          <ruby key={i}>
            {tok.t}
            <rt>{tok.r}</rt>
          </ruby>
        ) : (
          <span key={i}>{tok.t}</span>
        )
      )}
    </span>
  );
}
