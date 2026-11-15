'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { range } = require('../src/range.js');

test('counts up by 1', () => {
  assert.deepEqual(range(0, 4), [0, 1, 2, 3]);
});

test('counts up by a custom step', () => {
  assert.deepEqual(range(0, 10, 5), [0, 5]);
});
