const test = require('node:test');
const assert = require('node:assert/strict');

const { partitionPostsForEditorial } = require('../assets/js/app.js');

function makePost(index) {
  return {
    title: `Paper ${index}`,
    url: `/paper-${index}/`,
    date: `2026-04-0${index}`,
    categories: ['推荐'],
    description: `Description ${index}`
  };
}

test('partitionPostsForEditorial creates a lead story and two support stories on the default homepage', () => {
  const posts = [makePost(1), makePost(2), makePost(3), makePost(4), makePost(5)];

  const result = partitionPostsForEditorial(posts, {
    level1: null,
    level2: null,
    level3: null,
    searchQuery: ''
  });

  assert.equal(result.mode, 'editorial');
  assert.equal(result.lead.title, 'Paper 1');
  assert.deepEqual(result.support.map(post => post.title), ['Paper 2', 'Paper 3']);
  assert.deepEqual(result.archive.map(post => post.title), ['Paper 4', 'Paper 5']);
});

test('partitionPostsForEditorial falls back to a plain archive when filters are active', () => {
  const posts = [makePost(1), makePost(2), makePost(3)];

  const result = partitionPostsForEditorial(posts, {
    level1: '推荐',
    level2: null,
    level3: null,
    searchQuery: ''
  });

  assert.equal(result.mode, 'archive');
  assert.equal(result.lead, null);
  assert.deepEqual(result.support, []);
  assert.deepEqual(result.archive.map(post => post.title), ['Paper 1', 'Paper 2', 'Paper 3']);
});

test('partitionPostsForEditorial falls back to a plain archive when searching', () => {
  const posts = [makePost(1), makePost(2), makePost(3)];

  const result = partitionPostsForEditorial(posts, {
    level1: null,
    level2: null,
    level3: null,
    searchQuery: 'search'
  });

  assert.equal(result.mode, 'archive');
  assert.equal(result.lead, null);
  assert.deepEqual(result.support, []);
  assert.deepEqual(result.archive.map(post => post.title), ['Paper 1', 'Paper 2', 'Paper 3']);
});
