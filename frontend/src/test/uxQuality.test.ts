import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

function source(path: string): string {
  return readFileSync(join(process.cwd(), path), "utf8");
}

function mediaBlock(css: string, query: string): string {
  const start = css.indexOf(query);
  expect(start).toBeGreaterThanOrEqual(0);

  let depth = 0;
  let end = start;
  for (; end < css.length; end += 1) {
    const character = css[end];
    if (character === "{") {
      depth += 1;
    }
    if (character === "}") {
      depth -= 1;
      if (depth === 0) {
        return css.slice(start, end + 1);
      }
    }
  }

  return css.slice(start);
}

describe("frontend UX quality gates", () => {
  const css = source("src/styles/base.css");

  it("keeps keyboard focus visible across interactive controls", () => {
    expect(css).toContain(":focus-visible");
    expect(css).toContain("outline: 3px solid var(--color-signal)");
    expect(css).toContain("outline-offset: 3px");
    expect(css).toContain('[role="button"]');
    expect(css).toContain('[role="tab"]');
  });

  it("protects tablet layouts from horizontal overflow and crowded controls", () => {
    const tablet = mediaBlock(css, "@media (max-width: 920px)");

    expect(tablet).toContain(".app-shell");
    expect(tablet).toContain(".topbar");
    expect(tablet).toContain(".page-header");
    expect(tablet).toContain(".form-row");
    expect(tablet).toContain("grid-template-columns: 1fr");
    expect(tablet).toContain("flex-direction: column");
    expect(tablet).toContain("padding: 20px 16px 30px");
  });

  it("keeps dense data readable on small screens", () => {
    const tablet = mediaBlock(css, "@media (max-width: 920px)");
    const mobile = mediaBlock(css, "@media (max-width: 520px)");

    expect(tablet).toContain("table-layout: fixed");
    expect(tablet).toContain("overflow-wrap: anywhere");
    expect(tablet).toContain("white-space: normal");
    expect(mobile).toContain(".wallet-tabs");
    expect(mobile).toContain("width: 100%");
  });

  it("prevents fragile typography shortcuts", () => {
    expect(css).not.toMatch(/font-size:\s*[^;]*vw/);
    expect(css).not.toMatch(/letter-spacing:\s*-\d/);
  });
});
