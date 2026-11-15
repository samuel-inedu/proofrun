'use strict';

/**
 * Return the numbers from start to end. The end value is not included.
 */
function range(start, end, step = 1) {
  const out = [];
  for (let i = start; i < end; i += step) {
    out.push(i);
  }
  return out;
}

module.exports = { range };
