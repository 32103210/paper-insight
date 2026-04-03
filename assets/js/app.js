/**
 * Paper Insight - Knowledge Base JavaScript
 * Handles category navigation and search functionality
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

/**
 * Initialize the application
 */
function initApp() {
  renderCategoryTree();
  renderPosts(window.POSTS_DATA || []);
  initSearch();
  initBreadcrumb();
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
  const allItem = createCategoryItem('全部文章', 'all', null, (window.POSTS_DATA || []).length);
  allItem.classList.add('active');
  container.appendChild(allItem);

  // Render each top-level category
  const cats = window.CATEGORIES || {};
  Object.keys(cats).forEach(level1Name => {
    const level1 = cats[level1Name];
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

      container.appendChild(level2Ul);
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
    icon.className = 'icon';
    icon.textContent = '\u25B6'; // right arrow
    itemDiv.appendChild(icon);
  }

  const nameSpan = document.createElement('span');
  nameSpan.className = 'name';
  nameSpan.textContent = name;
  itemDiv.appendChild(nameSpan);

  const countSpan = document.createElement('span');
  countSpan.className = 'count';
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
  document.querySelectorAll('.category-item').forEach(el => el.classList.remove('active'));
  item.classList.add('active');

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

/**
 * Get filtered posts based on current state
 */
function getFilteredPosts() {
  return (window.POSTS_DATA || []).filter(post => {
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
      const titleMatch = post.title.toLowerCase().includes(query);
      const excerptMatch = post.excerpt && post.excerpt.toLowerCase().includes(query);
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

  breadcrumb.innerHTML = '';

  // Home link
  const homeLi = document.createElement('li');
  homeLi.innerHTML = '<a href="/">首页</a>';
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

  if (posts.length === 0) {
    container.innerHTML = '<p class="no-results">没有找到匹配的文章</p>';
    return;
  }

  container.innerHTML = posts.map(post => `
    <article class="post-card">
      <div class="post-card-header">
        <h3 class="post-card-title">
          <a href="${post.url}">${post.title}</a>
        </h3>
        <span class="post-card-date">${post.date}</span>
      </div>
      <div class="post-card-meta">
        <span class="arxiv-id">arXiv: ${post.arxiv_id}</span>
        ${post.tags ? post.tags.map(tag => `<span class="post-card-tag">${tag}</span>`).join('') : ''}
      </div>
      ${post.excerpt ? `<p class="post-card-excerpt">${post.excerpt}</p>` : ''}
    </article>
  `).join('');
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

// Initialize when DOM is ready
function doInit() {
  initApp();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', doInit);
} else {
  // DOM is already ready, but use setTimeout to ensure inline scripts have run
  setTimeout(doInit, 0);
}
