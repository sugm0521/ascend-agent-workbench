#!/usr/bin/env node
'use strict';

// Render two maintained Markdown documents; never collect or publish project data.
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

const escape = value => String(value).replace(/[&<>"']/g, c => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[c]));

function main() {
  const options = {};
  const allowed = new Set(['work', 'improvements', 'output', 'period', 'label']);
  const args = process.argv.slice(2);
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i]?.slice(2);
    if (!args[i]?.startsWith('--') || !allowed.has(key) || !args[i + 1] || options[key]) {
      throw new Error('Use --work <md> --improvements <md> --output <html> --period <range> [--label <text>]');
    }
    options[key] = args[i + 1];
  }
  for (const key of ['work', 'improvements', 'output', 'period']) {
    if (!options[key]) throw new Error(`Missing --${key}`);
  }
  const inputs = [options.work, options.improvements].map(p => path.resolve(p));
  const output = path.resolve(options.output);
  if (inputs.includes(output)) throw new Error('Output must not overwrite either Markdown input');
  if (fs.existsSync(output) && inputs.some(p => fs.realpathSync(p) === fs.realpathSync(output))) {
    throw new Error('Output resolves to a Markdown input');
  }
  const documents = inputs.map(p => {
    if (fs.statSync(p).size >= 1000000) throw new Error(`Input exceeds review size limit: ${p}`);
    const text = fs.readFileSync(p, 'utf8');
    if (!text.trim()) throw new Error(`Empty report: ${p}`);
    return text;
  });
  let Marked, Renderer;
  try { ({ Marked, Renderer } = require('marked')); }
  catch { throw new Error('Existing Node.js package "marked" is required; locate it with NODE_PATH or deliver Markdown only. Nothing was installed.'); }
  const renderer = new Renderer();
  renderer.html = token => escape(token.text);
  renderer.image = token => `<span class="image-note">（图片未嵌入：${escape(token.text || '')}）</span>`;
  renderer.link = function (token) {
    const text = this.parser.parseInline(token.tokens);
    let href = String(token.href || '').trim();
    if (/[\u0000-\u001f\u007f]/.test(href) || href.startsWith('//')) return text;
    if (/^[a-zA-Z]:[\\/]/.test(href)) href = pathToFileURL(href).href;
    let parsed;
    try { parsed = new URL(href, pathToFileURL(output)); } catch { return text; }
    if (!['http:', 'https:', 'file:'].includes(parsed.protocol)) return text;
    if (!href.startsWith('#')) href = parsed.href;
    return `<a href="${escape(href)}" rel="noreferrer">${text}</a>`;
  };
  const markdown = new Marked({ gfm: true, renderer });
  const article = (id, eyebrow, title, source) => {
    const body = source.replace(/^\uFEFF/, '').replace(/^# [^\r\n]+\r?\n/, '');
    // Resolve each document's own anchors separately inside the combined reader.
    const html = markdown.parse(body).replace(/href="#([^"]+)"/g, `href="#${id}-$1"`);
    const named = html.replace(/<h([2-6])>(.*?)<\/h\1>/g, (match, level, text) => {
      const anchor = text.replace(/<[^>]*>/g, '').trim().toLowerCase().replace(/[^\p{L}\p{N}-]+/gu, '-').replace(/^-|-$/g, '');
      return `<h${level} id="${id}-${escape(anchor)}">${text}</h${level}>`;
    });
    return `<article id="${id}" aria-labelledby="${id}-title"><header class="report-header"><p class="eyebrow">${eyebrow}</p><h2 id="${id}-title">${title}</h2></header><div class="prose">${named}</div></article>`;
  };
  const css = fs.readFileSync(path.join(__dirname, '..', 'assets', 'report.css'), 'utf8');
  const html = `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; base-uri 'none'; form-action 'none'"><title>工程周报 · ${escape(options.period)}</title><style>${css}</style></head>
<body><a class="skip" href="#work">跳到周报正文</a><div class="layout"><aside><div class="brand">WORKBENCH<span>每周工程记录</span></div><nav aria-label="两份周报"><a href="#work"><b>01</b> 个人工作周报</a><a href="#improvements"><b>02</b> 项目与知识库改进</a></nav><p class="local-note">本机阅读版<br>正文来自两份Markdown</p></aside><main><header class="cover"><p class="eyebrow">WEEKLY REVIEW</p><h1>本周工作与改进记录</h1><div class="meta"><span>${escape(options.period)}</span><span>${escape(options.label || '周报')}</span></div></header>
${article('work', 'REPORT 01 · WORK', '个人工作周报', documents[0])}
${article('improvements', 'REPORT 02 · IMPROVEMENT', '项目与知识库改进周报', documents[1])}
<footer class="page-footer">阅读顺序：本期结论 → 具体事项 → 验证与证据。报告状态以正文证据为准。</footer></main></div></body></html>`;
  if (Buffer.byteLength(html, 'utf8') >= 1000000) throw new Error('Rendered report exceeds 1MB; narrow this report before delivery');
  fs.mkdirSync(path.dirname(output), { recursive: true });
  const temporary = `${output}.${process.pid}.tmp`;
  try { fs.writeFileSync(temporary, html, 'utf8'); fs.renameSync(temporary, output); }
  finally { if (fs.existsSync(temporary)) fs.unlinkSync(temporary); }
  console.log(JSON.stringify({ output, bytes: Buffer.byteLength(html), inputs }));
}

try { main(); }
catch (error) { console.error(error.message); process.exitCode = 1; }
