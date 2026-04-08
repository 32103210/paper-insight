require 'jekyll'
require 'cgi'

module Jekyll
  # Generator for category pages
  class CategoryGenerator < Generator
    safe true

    def generate(site)
      # Collect all categories from posts
      categories = {}

      site.posts.each do |post|
        categories_for_post = Array(post.data['categories']).map(&:to_s).map(&:strip).reject(&:empty?).uniq
        next if categories_for_post.empty?

        categories_for_post.each do |category|
          categories[category] ||= []
          categories[category] << post
        end
      end

      # Generate category pages
      categories.each do |category, posts|
        site.pages << CategoryPage.new(site, site.source, category, posts)
      end
    end
  end

  # Category page class
  class CategoryPage < Page
    def initialize(site, base, category, posts)
      @site = site
      @base = base
      @dir = "category/#{CGI.escape(category)}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(base, '_layouts'), 'category.html')
      self.data['category'] = category
      self.data['posts'] = posts.sort_by(&:date).reverse
    end
  end
end
