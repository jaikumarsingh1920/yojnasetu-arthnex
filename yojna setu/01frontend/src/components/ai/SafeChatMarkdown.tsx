import React from 'react';

interface Props {
  content: string;
  isUser?: boolean;
  className?: string;
}

type Block =
  | { type: 'paragraph'; lines: string[] }
  | { type: 'bullet-list'; items: string[] }
  | { type: 'numbered-list'; items: { num: string; text: string }[] };

/**
 * Tokenizes a single line or text chunk to safely render inline markdown
 * (**bold**, *italic*, ***bold italic***) into standard React elements.
 * 
 * Safe native React DOM node rendering - 100% immune to injection.
 */
export const renderInlineMarkdown = (text: string, isUser = false, keyPrefix = 'inline'): React.ReactNode[] => {
  if (!text) return [];

  // Match bold-italic (***text***), bold (**text** or __text__), and italic (*text* or _text_)
  // Using negative lookahead/lookbehind to ensure asterisks/underscores are not surrounding spaces
  const tokenRegex = /(\*\*\*(?!\s).+?(?<!\s)\*\*\*|___(?!\s).+?(?<!\s)___|\*\*(?!\s).+?(?<!\s)\*\*|__(?!\s).+?(?<!\s)__|\*(?!\s)[^*]+?(?<!\s)\*|(?<![a-zA-Z0-9])_(?!\s)[^_]+?(?<!\s)_(?![a-zA-Z0-9]))/g;

  const parts = text.split(tokenRegex);
  const elements: React.ReactNode[] = [];

  parts.forEach((part, idx) => {
    if (!part) return;
    const key = `${keyPrefix}-${idx}`;

    // Bold + Italic (***text*** or ___text___)
    if ((part.startsWith('***') && part.endsWith('***') && part.length >= 6) ||
        (part.startsWith('___') && part.endsWith('___') && part.length >= 6)) {
      const inner = part.slice(3, -3);
      elements.push(
        <strong key={key} className={`font-bold ${isUser ? 'text-white' : 'text-slate-900'}`}>
          <em className="italic">{inner}</em>
        </strong>
      );
    }
    // Bold (**text** or __text__)
    else if ((part.startsWith('**') && part.endsWith('**') && part.length >= 4) ||
             (part.startsWith('__') && part.endsWith('__') && part.length >= 4)) {
      const inner = part.slice(2, -2);
      elements.push(
        <strong key={key} className={`font-bold ${isUser ? 'text-white' : 'text-slate-900'}`}>
          {renderInlineMarkdown(inner, isUser, `${key}-b`)}
        </strong>
      );
    }
    // Italic (*text* or _text_)
    else if ((part.startsWith('*') && part.endsWith('*') && part.length >= 2) ||
             (part.startsWith('_') && part.endsWith('_') && part.length >= 2)) {
      const inner = part.slice(1, -1);
      elements.push(
        <em key={key} className="italic">
          {inner}
        </em>
      );
    }
    // Plain text
    else {
      elements.push(part);
    }
  });

  return elements;
};

/**
 * Splits raw text into structured paragraph and list blocks.
 */
const parseBlocks = (rawText: string): Block[] => {
  const lines = rawText.split(/\r?\n/);
  const blocks: Block[] = [];
  let currentBlock: Block | null = null;

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      if (currentBlock) {
        blocks.push(currentBlock);
        currentBlock = null;
      }
      continue;
    }

    const bulletMatch = trimmed.match(/^[-*•+]\s+(.+)$/);
    const numberedMatch = trimmed.match(/^(\d+)[.)]\s+(.+)$/);

    if (bulletMatch) {
      if (currentBlock && currentBlock.type === 'bullet-list') {
        currentBlock.items.push(bulletMatch[1]);
      } else {
        if (currentBlock) blocks.push(currentBlock);
        currentBlock = { type: 'bullet-list', items: [bulletMatch[1]] };
      }
    } else if (numberedMatch) {
      if (currentBlock && currentBlock.type === 'numbered-list') {
        currentBlock.items.push({ num: numberedMatch[1], text: numberedMatch[2] });
      } else {
        if (currentBlock) blocks.push(currentBlock);
        currentBlock = {
          type: 'numbered-list',
          items: [{ num: numberedMatch[1], text: numberedMatch[2] }]
        };
      }
    } else {
      if (currentBlock && currentBlock.type === 'paragraph') {
        currentBlock.lines.push(rawLine);
      } else {
        if (currentBlock) blocks.push(currentBlock);
        currentBlock = { type: 'paragraph', lines: [rawLine] };
      }
    }
  }

  if (currentBlock) {
    blocks.push(currentBlock);
  }

  return blocks;
};

export const SafeChatMarkdown: React.FC<Props> = ({ content, isUser = false, className = '' }) => {
  if (!content) return null;

  const blocks = parseBlocks(content);

  return (
    <div className={`space-y-2 text-[11px] sm:text-xs font-sans leading-relaxed break-words ${className}`}>
      {blocks.map((block, bIdx) => {
        if (block.type === 'bullet-list') {
          return (
            <ul key={bIdx} className="my-1.5 space-y-1 list-none pl-0.5">
              {block.items.map((item, itemIdx) => (
                <li key={itemIdx} className="flex items-start gap-2 leading-relaxed">
                  <span
                    className={`inline-block w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
                      isUser ? 'bg-white/80' : 'bg-sky-600'
                    }`}
                    aria-hidden="true"
                  />
                  <span className="flex-1 min-w-0">
                    {renderInlineMarkdown(item, isUser, `b-${bIdx}-${itemIdx}`)}
                  </span>
                </li>
              ))}
            </ul>
          );
        }

        if (block.type === 'numbered-list') {
          return (
            <ol key={bIdx} className="my-1.5 space-y-1.5 list-none pl-0.5">
              {block.items.map((item, itemIdx) => (
                <li key={itemIdx} className="flex items-start gap-2 leading-relaxed">
                  <span
                    className={`inline-flex items-center justify-center min-w-[1.25rem] h-5 rounded-md text-[10px] font-bold shrink-0 mt-0.5 ${
                      isUser ? 'bg-white/20 text-white' : 'bg-sky-100 text-sky-900 border border-sky-200'
                    }`}
                    aria-hidden="true"
                  >
                    {item.num}
                  </span>
                  <span className="flex-1 min-w-0">
                    {renderInlineMarkdown(item.text, isUser, `nl-${bIdx}-${itemIdx}`)}
                  </span>
                </li>
              ))}
            </ol>
          );
        }

        // Paragraph block
        return (
          <p key={bIdx} className="leading-relaxed">
            {block.lines.map((line, lineIdx) => (
              <React.Fragment key={lineIdx}>
                {renderInlineMarkdown(line, isUser, `p-${bIdx}-${lineIdx}`)}
                {lineIdx < block.lines.length - 1 && <br />}
              </React.Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
};
