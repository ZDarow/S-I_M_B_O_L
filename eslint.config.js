/**
 * ESLint flat config для JS-модулей темы.
 * Правила: чистый код, запрет var, обязательные JSDoc.
 */

import js from '@eslint/js';
import globals from 'globals';

export default [
  js.configs.recommended,
  {
    files: ['book/theme/js/**/*.js'],
    ignores: ['book/theme/js/__tests__/**', 'book/theme/js/dtc-search.js', 'book/theme/js/service-tracker.js'],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.es2021,
      },
    },
    rules: {
      // Стиль
      'no-var': 'error',
      'prefer-const': 'error',
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'eqeqeq': ['error', 'always', { null: 'ignore' }],
      'curly': ['error', 'all'],
      'no-throw-literal': 'error',

      // Безопасность
      'no-eval': 'error',
      'no-implied-eval': 'error',
    },
  },
  {
    files: ['book/theme/js/__tests__/**/*.test.js'],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.es2021,
        ...globals.node,
      },
    },
    rules: {
      'no-console': 'off',
      'no-unused-vars': 'off',
    },
  },
  {
    files: ['vitest.config.js', 'eslint.config.js'],
    languageOptions: {
      sourceType: 'module',
      globals: {
        ...globals.node,
      },
    },
  },
  {
    // Легаси-виджеты (IIFE, глобальные переменные mdBook)
    files: ['book/theme/js/dtc-search.js', 'book/theme/js/service-tracker.js'],
    languageOptions: {
      sourceType: 'script',
      globals: {
        ...globals.browser,
        path_to_root: 'readonly',
      },
    },
    rules: {
      'no-empty': 'off',
      'no-unused-vars': 'off',
      'no-var': 'off',
    },
  },
];
