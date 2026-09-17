import React from 'react';
import type { DynamicFormField } from '../../types/activity-detail-mapper';
import './DynamicFormRenderer.css';

interface DynamicFormRendererProps {
  fields: DynamicFormField[];
  responses: Record<string, any>;
  onChange: (fieldLabel: string, value: any) => void;
  errors?: Record<string, string>;
  disabled?: boolean;
}

export const DynamicFormRenderer: React.FC<DynamicFormRendererProps> = ({
  fields,
  responses,
  onChange,
  errors = {},
  disabled = false,
}) => {
  if (!fields || fields.length === 0) return null;

  return (
    <div className="dynamic-form-container">
      {fields.map((field) => {
        const value = responses[field.label] ?? '';
        const errorMessage = errors[field.label];
        const inputId = `df_${field.id}`;

        return (
          <div
            key={field.id}
            className={`dynamic-form-group ${errorMessage ? 'dynamic-form-group--error' : ''}`}
          >
            <label htmlFor={inputId} className="dynamic-form-label">
              <span>{field.label}</span>
              {field.isRequired && <span className="dynamic-form-required" aria-hidden="true">*</span>}
            </label>

            {/* Field Type: Number */}
            {field.fieldType === 'number' && (
              <input
                id={inputId}
                type="number"
                className="dynamic-form-input"
                value={value}
                disabled={disabled}
                required={field.isRequired}
                onChange={(e) => onChange(field.label, e.target.valueAsNumber || e.target.value)}
                aria-invalid={!!errorMessage}
                aria-describedby={errorMessage ? `${inputId}_err` : undefined}
              />
            )}

            {/* Field Type: Textarea */}
            {field.fieldType === 'textarea' && (
              <textarea
                id={inputId}
                className="dynamic-form-textarea"
                rows={3}
                value={value}
                disabled={disabled}
                required={field.isRequired}
                onChange={(e) => onChange(field.label, e.target.value)}
                aria-invalid={!!errorMessage}
                aria-describedby={errorMessage ? `${inputId}_err` : undefined}
              />
            )}

            {/* Field Type: Select */}
            {field.fieldType === 'select' && field.options && field.options.length > 0 && (
              <select
                id={inputId}
                className="dynamic-form-select"
                value={value}
                disabled={disabled}
                required={field.isRequired}
                onChange={(e) => onChange(field.label, e.target.value)}
                aria-invalid={!!errorMessage}
                aria-describedby={errorMessage ? `${inputId}_err` : undefined}
              >
                <option value="">-- Chọn một phương án --</option>
                {field.options.map((opt, i) => (
                  <option key={i} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            )}

            {/* Field Type: Radio */}
            {field.fieldType === 'radio' && field.options && field.options.length > 0 && (
              <div className="dynamic-form-radio-group" role="radiogroup" aria-label={field.label}>
                {field.options.map((opt, i) => (
                  <label key={i} className="dynamic-form-radio-label">
                    <input
                      type="radio"
                      name={inputId}
                      value={opt}
                      checked={value === opt}
                      disabled={disabled}
                      onChange={() => onChange(field.label, opt)}
                    />
                    <span>{opt}</span>
                  </label>
                ))}
              </div>
            )}

            {/* Field Type: Checkbox (Boolean or Multi) */}
            {field.fieldType === 'checkbox' && (
              <label className="dynamic-form-checkbox-label">
                <input
                  id={inputId}
                  type="checkbox"
                  checked={!!value}
                  disabled={disabled}
                  onChange={(e) => onChange(field.label, e.target.checked)}
                />
                <span>Tôi đồng ý / Xác nhận</span>
              </label>
            )}

            {/* Default: Text input */}
            {(field.fieldType === 'text' ||
              (!['number', 'textarea', 'select', 'radio', 'checkbox'].includes(field.fieldType))) && (
              <input
                id={inputId}
                type="text"
                className="dynamic-form-input"
                value={value}
                disabled={disabled}
                required={field.isRequired}
                onChange={(e) => onChange(field.label, e.target.value)}
                aria-invalid={!!errorMessage}
                aria-describedby={errorMessage ? `${inputId}_err` : undefined}
              />
            )}

            {errorMessage && (
              <span id={`${inputId}_err`} className="dynamic-form-error" role="alert">
                {errorMessage}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default DynamicFormRenderer;
