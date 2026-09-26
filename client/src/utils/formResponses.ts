/**
 * Shared utility for retrieving form question responses reliably:
 * Priority:
 * 1. String(field.id)
 * 2. legacy field.label
 * 3. fallback "Chưa trả lời" or "-"
 */
export function getFormFieldResponse(
  field: { id?: string; label: string },
  formResponses?: Record<string, any> | null,
  fallback: string = 'Chưa trả lời'
): string {
  if (!formResponses || typeof formResponses !== 'object') {
    return fallback;
  }

  let rawVal: any = undefined;

  // 1. Primary: match by field.id
  if (field.id && formResponses[String(field.id)] !== undefined) {
    rawVal = formResponses[String(field.id)];
  }
  // 2. Legacy fallback: match by field.label
  else if (formResponses[field.label] !== undefined) {
    rawVal = formResponses[field.label];
  }

  if (rawVal === undefined || rawVal === null) {
    return fallback;
  }

  if (typeof rawVal === 'boolean') {
    return rawVal ? 'Có' : 'Không';
  }

  const str = String(rawVal).trim();
  return str.length > 0 ? str : fallback;
}
