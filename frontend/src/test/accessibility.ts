import { expect } from "vitest";

const INTERACTIVE_SELECTOR = [
  "a[href]",
  "button",
  "input:not([type='hidden'])",
  "select",
  "textarea",
  "[role='button']",
  "[role='link']",
  "[role='tab']",
].join(",");

export function expectNamedInteractiveElements(container: HTMLElement): void {
  const unnamed = Array.from(
    container.querySelectorAll<HTMLElement>(INTERACTIVE_SELECTOR),
  ).filter((element) => !accessibleName(element));

  expect(
    unnamed.map((element) => {
      const tag = element.tagName.toLowerCase();
      const id = element.getAttribute("id");
      const role = element.getAttribute("role");
      return [tag, id ? `#${id}` : "", role ? `[role="${role}"]` : ""].join("");
    }),
  ).toEqual([]);
}

export function expectValidAriaReferences(container: HTMLElement): void {
  const brokenReferences = Array.from(
    container.querySelectorAll<HTMLElement>(
      "[aria-describedby], [aria-labelledby]",
    ),
  ).flatMap((element) =>
    ["aria-describedby", "aria-labelledby"].flatMap((attribute) => {
      const value = element.getAttribute(attribute);
      if (!value) {
        return [];
      }
      return value
        .split(/\s+/)
        .filter(Boolean)
        .filter((id) => !element.ownerDocument.getElementById(id))
        .map((id) => `${element.tagName.toLowerCase()}[${attribute}="${id}"]`);
    }),
  );

  expect(brokenReferences).toEqual([]);
}

export function expectNoPositiveTabIndex(container: HTMLElement): void {
  const positiveTabStops = Array.from(
    container.querySelectorAll<HTMLElement>("[tabindex]"),
  ).filter((element) => {
    const value = Number(element.getAttribute("tabindex"));
    return Number.isFinite(value) && value > 0;
  });

  expect(
    positiveTabStops.map((element) => {
      const tag = element.tagName.toLowerCase();
      const id = element.getAttribute("id");
      const role = element.getAttribute("role");
      return [tag, id ? `#${id}` : "", role ? `[role="${role}"]` : ""].join("");
    }),
  ).toEqual([]);
}

function accessibleName(element: HTMLElement): string {
  const ariaLabel = element.getAttribute("aria-label")?.trim();
  if (ariaLabel) {
    return ariaLabel;
  }

  const labelledBy = element.getAttribute("aria-labelledby");
  if (labelledBy) {
    const label = labelledBy
      .split(/\s+/)
      .map((id) =>
        element.ownerDocument.getElementById(id)?.textContent?.trim(),
      )
      .filter(Boolean)
      .join(" ");
    if (label) {
      return label;
    }
  }

  const title = element.getAttribute("title")?.trim();
  if (title) {
    return title;
  }

  const id = element.getAttribute("id");
  if (id) {
    const explicitLabel = element.ownerDocument
      .querySelector(`label[for="${cssEscape(id)}"]`)
      ?.textContent?.trim();
    if (explicitLabel) {
      return explicitLabel;
    }
  }

  const wrappedLabel = element.closest("label")?.textContent?.trim();
  if (wrappedLabel) {
    return wrappedLabel;
  }

  return element.textContent?.trim() || "";
}

function cssEscape(value: string): string {
  return value.replace(/["\\]/g, "\\$&");
}
