/**
 * Shared validation utilities for CarbonIQ frontend forms.
 */

/**
 * Validates whether an email address has a valid frontend format.
 * 
 * Rules:
 * - Rejects empty input or non-string values.
 * - Trims accidental leading and trailing whitespace before validation.
 * - Requires a local part containing permitted characters (alphanumeric, dots, plus signs, underscores, hyphens).
 * - Requires an '@' separator.
 * - Requires a valid domain with a domain extension (at least 2 alphabetic characters).
 * - Rejects missing domains, missing TLDs, and addresses with whitespace.
 */
export function isValidEmail(email: string | null | undefined): boolean {
  if (!email || typeof email !== 'string') {
    return false
  }

  const trimmed = email.trim()
  if (!trimmed) {
    return false
  }

  // Practical frontend email validation pattern:
  // - Local part: [a-zA-Z0-9._%+-]+
  // - Domain name: [a-zA-Z0-9]+([.-][a-zA-Z0-9]+)*
  // - Domain extension: \.[a-zA-Z]{2,}
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9]+([.-][a-zA-Z0-9]+)*\.[a-zA-Z]{2,}$/

  return emailRegex.test(trimmed)
}
