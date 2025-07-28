export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
export const ALLOWED_FILE_TYPES = [
  'image/jpeg',
  'image/png', 
  'image/webp',
  'application/pdf'
];

export const validateFile = (file) => {
  const errors = [];

  if (file.size > MAX_FILE_SIZE) {
    errors.push(`File size must be less than ${MAX_FILE_SIZE / 1024 / 1024}MB`);
  }

  if (!ALLOWED_FILE_TYPES.includes(file.type)) {
    errors.push('File type not supported. Use JPEG, PNG, WebP, or PDF.');
  }

  // Check for potential PII in filename
  const piiPatterns = [/\b\d{3}-?\d{2}-?\d{4}\b/, /\b\d{9}\b/];
  if (piiPatterns.some(pattern => pattern.test(file.name))) {
    errors.push('Filename may contain sensitive information.');
  }

  return errors;
};

export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};