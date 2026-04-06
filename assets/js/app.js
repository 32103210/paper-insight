/**
 * Paper Insight
 * Handles editorial homepage composition, category navigation, search,
 * and lightweight shell interactions.
 */

// CATEGORIES and POSTS_DATA are populated by Jekyll Liquid tags in index.md
// We reference them via window to ensure we get the populated values

// Current filter state
let currentState = {
  level1: null,
  level2: null,
  level3: null,
  searchQuery: ''
};
let allPosts = [];
let categoriesTree = {};

function hasActiveFilters(state = currentState) {
  return Boolean(
    state.level1 ||
    state.level2 ||
    state.level3 ||
    (state.searchQuery || '').trim()
  );
}

function normalizePosts(posts) {
  return posts.map(post => {
    const categories = Array.isArray(post.categories)
      ? [...new Set(post.categories.filter(Boolean))]
      : [];
    const excerpt = post.excerpt || post.description || '';

    return {
      ...post,
      categories,
      description: post.description || excerpt,
      excerpt
    };
  });
}

function buildCategoryTree(posts) {
  const tree = {};

  posts.forEach(post => {
    const [level1, level2, level3] = post.categories || [];
    if (!level1) return;

    if (!tree[level1]) {
      tree[level1] = { children: {}, posts: [] };
    }
    tree[level1].posts.push(post);

    if (!level2) return;

    if (!tree[level1].children[level2]) {
      tree[level1].children[level2] = { children: {}, posts: [] };
    }
    tree[level1].children[level2].posts.push(post);

    if (!level3) return;

    if (!tree[level1].children[level2].children[level3]) {
      tree[level1].children[level2].children[level3] = { posts: [] };
    }
    tree[level1].children[level2].children[level3].posts.push(post);
  });

  return tree;
}

function partitionPostsForEditorial(posts, state = currentState) {
  if (!Array.isArray(posts) || posts.length === 0) {
    return {
      mode: 'empty',
      lead: null,
      support: [],
      archive: []
    };
  }

  if (hasActiveFilters(state)) {
    return {
      mode: 'archive',
      lead: null,
      support: [],
      archive: posts
    };
  }

  return {
    mode: 'editorial',
    lead: posts[0] || null,
    support: posts.slice(1, 3),
    archive: posts.slice(3)
  };
}

function renderTags(tags, className) {
  if (!tags || tags.length === 0) return '';

  return `
    <div class="${className}">
      ${tags.map(tag => `<span class="${className}-item">${tag}</span>`).join('')}
    </div>
  `;
}

function renderPostCard(post, variant = 'archive') {
  const meta = [];
  if (post.date) {
    meta.push(`<span class="post-card-date">${post.date}</span>`);
  }
  if (post.arxiv_id) {
    meta.push(`<span class="post-card-arxiv">arXiv ${post.arxiv_id}</span>`);
  }

  return `
    <article class="post-card post-card-${variant}">
      <div class="post-card-frame">
        <div class="post-card-meta">${meta.join('')}</div>
        <h3 class="post-card-title">
          <a href="${post.url}">${post.title}</a>
        </h3>
        ${(post.description || post.excerpt) ? `<p class="post-card-excerpt">${post.description || post.excerpt}</p>` : ''}
        ${renderTags(post.tags || post.categories || [], 'post-card-tags')}
      </div>
    </article>
  `;
}

function renderEditorialStream(posts) {
  const sections = partitionPostsForEditorial(posts);

  if (sections.mode === 'empty') {
    return '<p class="no-results">没有找到匹配的文章</p>';
  }

  if (sections.mode === 'archive') {
    return `
      <div class="editorial-results">
        <div class="editorial-results-header">
          <span class="editorial-results-kicker">Filtered Archive</span>
          <h2 class="editorial-results-title">当前检索结果</h2>
        </div>
        <div class="post-archive-list">
          ${sections.archive.map(post => renderPostCard(post, 'archive')).join('')}
        </div>
      </div>
    `;
  }

  return `
    <section class="editorial-lead">
      ${sections.lead ? renderPostCard(sections.lead, 'lead') : ''}
    </section>
    <section class="editorial-support">
      ${sections.support.map(post => renderPostCard(post, 'support')).join('')}
    </section>
    <section class="editorial-archive">
      <div class="section-intro">
        <span class="section-kicker">Research Archive</span>
        <h2 class="section-title">最新论文目录</h2>
      </div>
      <div class="post-archive-list">
        ${sections.archive.map(post => renderPostCard(post, 'archive')).join('')}
      </div>
    </section>
  `;
}

/**
 * Initialize the application
 */
function initApp() {
  allPosts = normalizePosts(window.POSTS_DATA || []);
  if (allPosts.length === 0) return;

  categoriesTree = buildCategoryTree(allPosts);
  window.POSTS_DATA = allPosts;
  window.CATEGORIES = categoriesTree;

  renderCategoryTree();
  initSearch();
  initBreadcrumb();

  if (!applyPathFilterFromUrl()) {
    renderPosts(allPosts);
  }
}

/**
 * Initialize breadcrumb click handler (called once)
 */
function initBreadcrumb() {
  const breadcrumb = document.getElementById('breadcrumb');
  if (!breadcrumb) return;

  // Use event delegation - listener added once at init
  breadcrumb.addEventListener('click', (e) => {
    const link = e.target.closest('a[data-path]');
    if (link) {
      e.preventDefault();
      const path = link.dataset.path;
      const item = document.querySelector(`.category-item[data-path="${path}"]`);
      if (item) item.click();
    }
  });
}

/**
 * Render the category tree from CATEGORIES object
 */
function renderCategoryTree() {
  const container = document.getElementById('category-tree');
  if (!container) return;

  container.innerHTML = '';

  // Add "All Posts" option
  const allItem = createCategoryItem('全部文章', 'all', null, allPosts.length);
  allItem.classList.add('active');
  container.appendChild(allItem);

  // Render each top-level category
  Object.keys(categoriesTree).forEach(level1Name => {
    const level1 = categoriesTree[level1Name];
    const level1Count = countPostsAtLevel(level1);

    const level1Item = createCategoryItem(level1Name, 'level1', level1Name, level1Count);
    container.appendChild(level1Item);

    // Level 2 categories
    if (level1.children) {
      const level2Ul = document.createElement('ul');
      level2Ul.className = 'category-children';

      Object.keys(level1.children).forEach(level2Name => {
        const level2 = level1.children[level2Name];
        const level2Count = countPostsAtLevel(level2);

        const level2Item = createCategoryItem(level2Name, 'level2', `${level1Name}|${level2Name}`, level2Count);
          level2Ul.appendChild(level2Item);

        // Level 3 categories
        if (level2.children) {
          const level3Ul = document.createElement('ul');
          level3Ul.className = 'category-children';

          Object.keys(level2.children).forEach(level3Name => {
            const level3 = level2.children[level3Name];
            const level3Count = level3.posts ? level3.posts.length : 0;

            const level3Item = createCategoryItem(level3Name, 'level3', `${level1Name}|${level2Name}|${level3Name}`, level3Count);
            level3Ul.appendChild(level3Item);
          });

          level2Item.appendChild(level3Ul);
        }
      });

      level1Item.appendChild(level2Ul);
    }
  });

  // Add click handlers
  attachCategoryListeners();
}

/**
 * Create a category item element
 */
function createCategoryItem(name, level, path, count) {
  const li = document.createElement('li');
  li.className = `category-${level}`;

  const itemDiv = document.createElement('div');
  itemDiv.className = 'category-item';
  itemDiv.dataset.level = level;
  itemDiv.dataset.path = path || 'all';

  if (level !== 'all') {
    const icon = document.createElement('span');
    icon.className = 'category-toggle';
    icon.textContent = '\u25B6'; // right arrow
    itemDiv.appendChild(icon);
  }

  const nameSpan = document.createElement('span');
  nameSpan.className = 'category-name';
  nameSpan.textContent = name;
  itemDiv.appendChild(nameSpan);

  const countSpan = document.createElement('span');
  countSpan.className = 'category-count';
  countSpan.textContent = count;
  itemDiv.appendChild(countSpan);

  li.appendChild(itemDiv);

  return li;
}

/**
 * Count posts at a category level
 */
function countPostsAtLevel(category) {
  if (category.posts) {
    return category.posts.length;
  }
  if (category.children) {
    let total = 0;
    Object.keys(category.children).forEach(childName => {
      total += countPostsAtLevel(category.children[childName]);
    });
    return total;
  }
  return 0;
}

/**
 * Attach click listeners to category items
 */
function attachCategoryListeners() {
  document.querySelectorAll('.category-item').forEach(item => {
    item.addEventListener('click', handleCategoryClick);
  });
}

/**
 * Handle category item click
 */
function handleCategoryClick(e) {
  const item = e.currentTarget;
  const level = item.dataset.level;
  const path = item.dataset.path;

  // Update state
  if (level === 'all') {
    currentState = { level1: null, level2: null, level3: null, searchQuery: currentState.searchQuery };
  } else if (level === 'level1') {
    currentState = { level1: path, level2: null, level3: null, searchQuery: currentState.searchQuery };
  } else if (level === 'level2') {
    const parts = path.split('|');
    currentState = { level1: parts[0], level2: parts[1], level3: null, searchQuery: currentState.searchQuery };
  } else if (level === 'level3') {
    const parts = path.split('|');
    currentState = { level1: parts[0], level2: parts[1], level3: parts[2], searchQuery: currentState.searchQuery };
  }

  // Update active state
  setActiveCategoryItem(path);

  // Handle expand/collapse
  const parentLi = item.parentElement;
  const childUl = parentLi.querySelector(':scope > .category-children');

  if (childUl) {
    parentLi.classList.toggle('expanded');
    item.classList.toggle('expanded');
    childUl.classList.toggle('expanded');
  }

  // Update breadcrumb
  updateBreadcrumb();

  // Filter and render posts
  renderPosts(getFilteredPosts());
}

function setStateFromPath(path) {
  const parts = String(path || '').split('|').filter(Boolean);

  currentState = {
    level1: parts[0] || null,
    level2: parts[1] || null,
    level3: parts[2] || null,
    searchQuery: currentState.searchQuery
  };
}

function setActiveCategoryItem(path) {
  const targetPath = path || 'all';

  document.querySelectorAll('.category-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.category-children').forEach(el => el.classList.remove('expanded'));
  document.querySelectorAll('.category-item.expanded').forEach(el => el.classList.remove('expanded'));

  const target = Array.from(document.querySelectorAll('.category-item'))
    .find(el => el.dataset.path === targetPath);

  if (target) {
    target.classList.add('active');

    let node = target.parentElement;
    while (node) {
      const childList = node.classList?.contains('category-children') ? node : null;
      if (childList) {
        childList.classList.add('expanded');
        const parentItem = childList.parentElement?.querySelector(':scope > .category-item');
        if (parentItem) {
          parentItem.classList.add('expanded');
        }
      }
      node = node.parentElement;
    }
  }
}

function applyPathFilterFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const path = params.get('path');

  if (!path) {
    return false;
  }

  setStateFromPath(path);
  setActiveCategoryItem(path);
  updateBreadcrumb();
  renderPosts(getFilteredPosts());
  return true;
}

/**
 * Get filtered posts based on current state
 */
function getFilteredPosts() {
  return allPosts.filter(post => {
    // Category filter
    if (currentState.level1) {
      if (!post.categories || !post.categories.includes(currentState.level1)) {
        return false;
      }
      if (currentState.level2 && (!post.categories || !post.categories.includes(currentState.level2))) {
        return false;
      }
      if (currentState.level3 && (!post.categories || !post.categories.includes(currentState.level3))) {
        return false;
      }
    }

    // Search filter
    if (currentState.searchQuery) {
      const query = currentState.searchQuery.toLowerCase();
      const titleMatch = (post.title || '').toLowerCase().includes(query);
      const excerptMatch = (post.description || post.excerpt || '').toLowerCase().includes(query);
      if (!titleMatch && !excerptMatch) {
        return false;
      }
    }

    return true;
  });
}

/**
 * Update breadcrumb based on current state
 */
function updateBreadcrumb() {
  const breadcrumb = document.getElementById('breadcrumb');
  if (!breadcrumb) return;
  const homeUrl = document.querySelector('.sidebar-header a')?.getAttribute('href') || '/';

  breadcrumb.innerHTML = '';

  // Home link
  const homeLi = document.createElement('li');
  homeLi.innerHTML = `<a href="${homeUrl}">首页</a>`;
  breadcrumb.appendChild(homeLi);

  if (currentState.level1) {
    const sep1 = document.createElement('li');
    sep1.className = 'separator';
    sep1.textContent = '/';
    breadcrumb.appendChild(sep1);

    const level1Li = document.createElement('li');
    level1Li.innerHTML = `<a href="#" data-path="${currentState.level1}">${currentState.level1}</a>`;
    breadcrumb.appendChild(level1Li);

    if (currentState.level2) {
      const sep2 = document.createElement('li');
      sep2.className = 'separator';
      sep2.textContent = '/';
      breadcrumb.appendChild(sep2);

      const level2Li = document.createElement('li');
      level2Li.innerHTML = `<a href="#" data-path="${currentState.level1}|${currentState.level2}">${currentState.level2}</a>`;
      breadcrumb.appendChild(level2Li);

      if (currentState.level3) {
        const sep3 = document.createElement('li');
        sep3.className = 'separator';
        sep3.textContent = '/';
        breadcrumb.appendChild(sep3);

        const level3Li = document.createElement('li');
        level3Li.className = 'current';
        level3Li.textContent = currentState.level3;
        breadcrumb.appendChild(level3Li);
      } else {
        const currentLi = document.createElement('li');
        currentLi.className = 'current';
        currentLi.textContent = currentState.level2;
        breadcrumb.appendChild(currentLi);
      }
    } else {
      const currentLi = document.createElement('li');
      currentLi.className = 'current';
      currentLi.textContent = currentState.level1;
      breadcrumb.appendChild(currentLi);
    }
  } else {
    const sep = document.createElement('li');
    sep.className = 'separator';
    sep.textContent = '/';
    breadcrumb.appendChild(sep);

    const currentLi = document.createElement('li');
    currentLi.className = 'current';
    currentLi.textContent = '全部文章';
    breadcrumb.appendChild(currentLi);
  }
}

/**
 * Render posts to the container
 */
function renderPosts(posts) {
  const container = document.getElementById('posts-container');
  if (!container) return;

  container.innerHTML = renderEditorialStream(posts);
}

/**
 * Initialize search functionality
 */
function initSearch() {
  const searchInput = document.getElementById('search-input');
  if (!searchInput) return;

  let debounceTimer;

  searchInput.addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      currentState.searchQuery = e.target.value.trim();
      renderPosts(getFilteredPosts());
    }, 300);
  });
}

function initSidebarChrome() {
  const body = document.body;
  const toggle = document.querySelector('.sidebar-toggle');
  const dismissors = document.querySelectorAll('[data-sidebar-dismiss]');

  if (!body || !toggle) return;

  const closeSidebar = () => {
    body.classList.remove('sidebar-open');
    toggle.setAttribute('aria-expanded', 'false');
  };

  const openSidebar = () => {
    body.classList.add('sidebar-open');
    toggle.setAttribute('aria-expanded', 'true');
  };

  toggle.addEventListener('click', () => {
    if (body.classList.contains('sidebar-open')) {
      closeSidebar();
    } else {
      openSidebar();
    }
  });

  dismissors.forEach(node => {
    node.addEventListener('click', closeSidebar);
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeSidebar();
    }
  });
}

// Initialize when DOM is ready
function doInit() {
  initSidebarChrome();

  const hasHomeScaffold =
    Boolean(document.getElementById('search-input')) &&
    Boolean(document.getElementById('breadcrumb')) &&
    Boolean(document.getElementById('posts-container'));
  const hasBootstrappedPosts = Array.isArray(window.POSTS_DATA) && window.POSTS_DATA.length > 0;

  if (!hasHomeScaffold || !hasBootstrappedPosts) {
    return;
  }

  initApp();
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', doInit);
  } else {
    // DOM is already ready, but use setTimeout to ensure inline scripts have run
    setTimeout(doInit, 0);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    buildCategoryTree,
    hasActiveFilters,
    normalizePosts,
    partitionPostsForEditorial
  };
}
