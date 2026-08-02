/**
 * 轻量 Markdown 渲染器：无外部依赖，所有文本先转义再拼装，避免 XSS。
 * 支持标题、列表、表格、引用、围栏代码块、行内代码、粗斜体、链接。
 */

const KEYWORDS = new Set([
  "abstract","as","async","await","boolean","break","case","catch","class","const","continue",
  "def","default","del","delete","do","elif","else","except","export","extends","False","finally",
  "float","for","from","func","function","go","if","import","in","instanceof","int","interface",
  "is","lambda","let","new","nil","None","not","null","or","package","pass","print","private",
  "public","raise","return","self","static","str","struct","super","switch","this","throw","True",
  "true","false","try","type","typeof","var","void","while","with","yield","and","elseif","end",
]);

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

/** 对已转义的代码做粗粒度着色：注释 / 字符串 / 数字 / 关键字。 */
function highlight(escapedCode) {
  const tokenPattern =
    /(&quot;(?:[^&\\]|\\.|&(?!quot;))*&quot;|&#39;(?:[^&\\]|\\.|&(?!#39;))*&#39;|`[^`]*`)|(#[^\n]*|\/\/[^\n]*)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_][A-Za-z0-9_]*)/g;

  return escapedCode.replace(tokenPattern, (match, str, comment, num, word) => {
    if (str) return `<span class="tok-str">${str}</span>`;
    if (comment) return `<span class="tok-com">${comment}</span>`;
    if (num) return `<span class="tok-num">${num}</span>`;
    if (word && KEYWORDS.has(word)) return `<span class="tok-key">${word}</span>`;
    return match;
  });
}

function stabilizeInlineMarkdown(text) {
  let out = String(text);
  if ((out.match(/\*\*/g) || []).length % 2 === 1) out += "**";
  if ((out.match(/~~/g) || []).length % 2 === 1) out += "~~";
  let ticks = 0;
  for (let i = 0; i < out.length; i += 1) {
    if (out[i] === "`") ticks += 1;
  }
  if (ticks % 2 === 1) out += "`";
  return out;
}

function renderInline(text, streaming = false) {
  const source = streaming ? stabilizeInlineMarkdown(text) : text;
  let out = escapeHtml(source);

  out = out.replace(/`([^`]+)`/g, (_, code) => `<code class="md-code">${code}</code>`);
  out = out.replace(/\*\*([^*]+)\*\*/g, '<strong class="md-key">$1</strong>');
  out = out.replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>");
  out = out.replace(/~~([^~]+)~~/g, "<del>$1</del>");
  out = out.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
  );
  return out;
}

const CALLOUT_RE = /^(?:\*\*)?(结论|根因|原因|建议|关键发现|核心结论|总结)(?:\*\*)?[：:]/;
const KPI_RE = /(\b(?:ROI|消耗|花费|转化|预算|CTR|CVR|CPA|ROAS)\b[^<\d]{0,6})(\d+(?:\.\d+)?%?)/gi;

function highlightMetrics(html) {
  return html.replace(KPI_RE, (_m, label, value) => `${label}<span class="md-kpi">${value}</span>`);
}

function emphasizeReply(html) {
  let out = highlightMetrics(html);

  out = out.replace(/<p>([\s\S]*?)<\/p>/g, (match, inner) => {
    const plain = inner.replace(/<[^>]+>/g, "");
    if (CALLOUT_RE.test(plain)) {
      return `<p class="md-callout">${inner}</p>`;
    }
    if (/^(?:\*\*)?(?:综上|总的来说|一句话)/.test(plain)) {
      return `<p class="md-lead">${inner}</p>`;
    }
    return match;
  });

  out = out.replace(/<h[34] class="md-h">([^<]*(?:结论|根因|建议|关键发现)[^<]*)<\/h[34]>/g, (match) =>
    match.replace('class="md-h"', 'class="md-h md-callout-heading"')
  );

  return out;
}

function renderTable(rows) {
  const cells = (line) =>
    line
      .replace(/^\s*\|/, "")
      .replace(/\|\s*$/, "")
      .split("|")
      .map((c) => c.trim());

  const head = cells(rows[0]);
  const body = rows.slice(2).map(cells);

  const thead = `<thead><tr>${head.map((c) => `<th>${renderInline(c)}</th>`).join("")}</tr></thead>`;
  const tbody = `<tbody>${body
    .map((row) => `<tr>${row.map((c) => `<td>${renderInline(c)}</td>`).join("")}</tr>`)
    .join("")}</tbody>`;

  return `<div class="md-table-wrap"><table class="md-table">${thead}${tbody}</table></div>`;
}

function renderStreamingFence(lang, lines) {
  const raw = lines.join("\n");
  return (
    `<div class="md-pre md-pre-streaming">` +
    `<div class="md-pre-bar"><span class="md-pre-lang">${escapeHtml(lang || "code")}</span></div>` +
    `<pre><code>${highlight(escapeHtml(raw))}</code></pre></div>`
  );
}

function isTableDivider(line) {
  return /^\s*\|?[\s:-]*-[-\s:|]*\|?\s*$/.test(line) && line.includes("-");
}

export function renderMarkdown(source, options = {}) {
  const streaming = Boolean(options.streaming);
  const lines = String(source || "").split("\n");
  const html = [];

  let listType = null;
  let paragraph = [];
  let inFence = false;
  let fenceLang = "";
  let fenceBuffer = [];

  const flushParagraph = () => {
    if (!paragraph.length) return;
    html.push(`<p>${renderInline(paragraph.join(" "), streaming)}</p>`);
    paragraph = [];
  };

  const closeList = () => {
    if (listType) {
      html.push(listType === "ul" ? "</ul>" : "</ol>");
      listType = null;
    }
  };

  const flushOpenFence = () => {
    if (!inFence) return;
    html.push(renderStreamingFence(fenceLang, fenceBuffer));
    inFence = false;
    fenceLang = "";
    fenceBuffer = [];
  };

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];

    const fence = line.match(/^\s*```(\w*)\s*$/);
    if (fence) {
      if (inFence) {
        const raw = fenceBuffer.join("\n");
        html.push(
          `<div class="md-pre" data-code="${escapeHtml(raw)}">` +
            `<div class="md-pre-bar"><span class="md-pre-lang">${escapeHtml(fenceLang || "code")}</span>` +
            `<button type="button" class="md-copy" title="复制代码">复制</button></div>` +
            `<pre><code>${highlight(escapeHtml(raw))}</code></pre></div>`
        );
        inFence = false;
        fenceLang = "";
        fenceBuffer = [];
        continue;
      }
      flushParagraph();
      closeList();
      inFence = true;
      fenceLang = fence[1] || "";
      fenceBuffer = [];
      continue;
    }

    if (inFence) {
      fenceBuffer.push(line);
      continue;
    }

    if (!line.trim()) {
      flushParagraph();
      closeList();
      continue;
    }

    if (
      line.includes("|") &&
      i + 1 < lines.length &&
      isTableDivider(lines[i + 1]) &&
      /\|/.test(lines[i + 1])
    ) {
      flushParagraph();
      closeList();
      const block = [];
      while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {
        block.push(lines[i]);
        i += 1;
      }
      i -= 1;
      html.push(renderTable(block));
      continue;
    }

    const heading = line.match(/^(#{1,4})\s+(.*)$/);
    if (heading) {
      flushParagraph();
      closeList();
      const level = Math.min(heading[1].length + 2, 6);
      html.push(`<h${level} class="md-h">${renderInline(heading[2], streaming)}</h${level}>`);
      continue;
    }

    if (/^\s*(---|\*\*\*|___)\s*$/.test(line)) {
      flushParagraph();
      closeList();
      html.push('<hr class="md-hr" />');
      continue;
    }

    const quote = line.match(/^\s*>\s?(.*)$/);
    if (quote) {
      flushParagraph();
      closeList();
      html.push(`<blockquote class="md-quote">${renderInline(quote[1], streaming)}</blockquote>`);
      continue;
    }

    const bullet = line.match(/^\s*[-*+]\s+(.*)$/);
    const ordered = line.match(/^\s*\d+\.\s+(.*)$/);
    if (bullet || ordered) {
      flushParagraph();
      const wanted = bullet ? "ul" : "ol";
      if (listType !== wanted) {
        closeList();
        html.push(wanted === "ul" ? '<ul class="md-list">' : '<ol class="md-list">');
        listType = wanted;
      }
      html.push(`<li>${renderInline((bullet || ordered)[1], streaming)}</li>`);
      continue;
    }

    closeList();
    paragraph.push(line.trim());
  }

  flushParagraph();
  closeList();
  if (streaming && inFence) flushOpenFence();
  return emphasizeReply(html.join(""));
}

export { escapeHtml };
