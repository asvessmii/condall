import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Telegram Web App initialization
const initTelegramWebApp = () => {
  if (window.Telegram?.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    tg.enableClosingConfirmation();
    
    // Set theme
    tg.setHeaderColor('#2196F3');
    tg.setBackgroundColor('#ffffff');
    
    console.log('Telegram Web App initialized');
    return tg;
  }
  return null;
};

// Get Telegram user data
const getTelegramUser = () => {
  if (window.Telegram?.WebApp?.initDataUnsafe?.user) {
    return window.Telegram.WebApp.initDataUnsafe.user;
  }
  return null;
};

// Bottom Navigation Component
const BottomNavigation = ({ activeSection, setActiveSection, cartCount }) => {
  const menuItems = [
    { id: 'catalog', name: 'Каталог', icon: '🏪' },
    { id: 'about', name: 'О нас', icon: '📋' },
    { id: 'feedback', name: 'Связь', icon: '💬' },
    { id: 'cart', name: 'Корзина', icon: '🛒', badge: cartCount }
  ];

  return (
    <nav className="bottom-nav">
      <div className="bottom-nav-container">
        {menuItems.map(item => (
          <button
            key={item.id}
            onClick={() => setActiveSection(item.id)}
            className={`bottom-nav-item ${
              activeSection === item.id ? 'active' : ''
            }`}
          >
            <div className="bottom-nav-icon">
              <span className="icon">{item.icon}</span>
              {item.badge > 0 && (
                <span className="badge">{item.badge}</span>
              )}
            </div>
            <span className="bottom-nav-text">{item.name}</span>
          </button>
        ))}
      </div>
    </nav>
  );
};

// Header Component
const Header = ({ title = "КЛИМАТ ТЕХНО" }) => {
  return (
    <header className="app-header">
      <div className="header-content">
        <h1 className="header-title">
          <span className="header-icon">❄️</span>
          {title}
        </h1>
      </div>
    </header>
  );
};

// Product Card Component
const ProductCard = ({ product, onViewDetails, onAddToCart }) => {
  return (
    <div className="product-card">
      <div className="product-image-container">
        <img 
          src={product.image_url} 
          alt={product.name}
          className="product-image"
        />
      </div>
      <div className="product-info">
        <h3 className="product-name">{product.name}</h3>
        <p className="product-description">{product.short_description}</p>
        <div className="product-price">
          {product.price.toLocaleString()} ₽
        </div>
        <div className="product-actions">
          <button
            onClick={() => onViewDetails(product)}
            className="btn btn-secondary"
          >
            Подробнее
          </button>
          <button
            onClick={() => onAddToCart(product)}
            className="btn btn-primary"
          >
            В корзину
          </button>
        </div>
      </div>
    </div>
  );
};

// Product Details Modal
const ProductDetailsModal = ({ product, onClose, onAddToCart }) => {
  if (!product) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">{product.name}</h2>
          <button onClick={onClose} className="modal-close">×</button>
        </div>
        <div className="modal-content">
          <div className="product-detail-image">
            <img src={product.image_url} alt={product.name} />
          </div>
          <div className="product-detail-info">
            <p className="product-detail-description">{product.description}</p>
            <div className="product-detail-price">
              {product.price.toLocaleString()} ₽
            </div>
            <button
              onClick={() => {
                onAddToCart(product);
                onClose();
              }}
              className="btn btn-primary btn-large"
            >
              Добавить в корзину
            </button>
          </div>
          {product.specifications && Object.keys(product.specifications).length > 0 && (
            <div className="specifications">
              <h3 className="specifications-title">Характеристики</h3>
              <div className="specifications-list">
                {Object.entries(product.specifications).map(([key, value]) => (
                  <div key={key} className="specification-item">
                    <span className="spec-key">{key}</span>
                    <span className="spec-value">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Filters Component
const ProductFilters = ({ products, filters, onFiltersChange, onReset }) => {
  const [showFilters, setShowFilters] = useState(false);

  // Extract unique values for filters
  const brands = [...new Set(products.map(p => {
    const brandMatch = p.name.match(/^([A-Za-z\s]+)/);
    return brandMatch ? brandMatch[1].trim() : 'Другие';
  }))];

  const powerOptions = [...new Set(products.map(p => {
    const power = p.specifications?.['Мощность охлаждения'];
    return power ? power.replace(' кВт', '') : null;
  }).filter(Boolean))].sort((a, b) => parseFloat(a) - parseFloat(b));

  const areaOptions = [...new Set(products.map(p => {
    const area = p.specifications?.['Площадь помещения'];
    return area ? area.replace(' м²', '') : null;
  }).filter(Boolean))].sort((a, b) => parseInt(a) - parseInt(b));

  const efficiencyClasses = [...new Set(products.map(p => 
    p.specifications?.['Класс энергоэффективности']
  ).filter(Boolean))];

  const handleFilterChange = (key, value) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const handlePriceChange = (key, value) => {
    onFiltersChange({
      ...filters,
      priceRange: { ...filters.priceRange, [key]: value }
    });
  };

  const activeFiltersCount = Object.entries(filters).filter(([key, value]) => {
    if (key === 'priceRange') {
      return value.min || value.max;
    }
    return value && value.length > 0;
  }).length;

  return (
    <div className="filters-container">
      <div className="filters-header">
        <div className="search-container">
          <input
            type="text"
            placeholder="Поиск кондиционеров..."
            value={filters.search || ''}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            className="search-input"
          />
          <span className="search-icon">🔍</span>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`filters-toggle ${activeFiltersCount > 0 ? 'has-filters' : ''}`}
        >
          <span>Фильтры</span>
          {activeFiltersCount > 0 && (
            <span className="filters-count">{activeFiltersCount}</span>
          )}
          <span className={`toggle-icon ${showFilters ? 'open' : ''}`}>▼</span>
        </button>
      </div>

      {showFilters && (
        <div className="filters-panel">
          <div className="filters-grid">
            {/* Brand Filter */}
            <div className="filter-group">
              <label className="filter-label">Производитель</label>
              <select
                value={filters.brand || ''}
                onChange={(e) => handleFilterChange('brand', e.target.value)}
                className="filter-select"
              >
                <option value="">Все производители</option>
                {brands.map(brand => (
                  <option key={brand} value={brand}>{brand}</option>
                ))}
              </select>
            </div>

            {/* Power Filter */}
            <div className="filter-group">
              <label className="filter-label">Мощность охлаждения</label>
              <select
                value={filters.power || ''}
                onChange={(e) => handleFilterChange('power', e.target.value)}
                className="filter-select"
              >
                <option value="">Любая мощность</option>
                {powerOptions.map(power => (
                  <option key={power} value={power}>{power} кВт</option>
                ))}
              </select>
            </div>

            {/* Area Filter */}
            <div className="filter-group">
              <label className="filter-label">Площадь помещения</label>
              <select
                value={filters.area || ''}
                onChange={(e) => handleFilterChange('area', e.target.value)}
                className="filter-select"
              >
                <option value="">Любая площадь</option>
                {areaOptions.map(area => (
                  <option key={area} value={area}>{area} м²</option>
                ))}
              </select>
            </div>

            {/* Efficiency Filter */}
            <div className="filter-group">
              <label className="filter-label">Класс энергоэффективности</label>
              <select
                value={filters.efficiency || ''}
                onChange={(e) => handleFilterChange('efficiency', e.target.value)}
                className="filter-select"
              >
                <option value="">Любой класс</option>
                {efficiencyClasses.map(cls => (
                  <option key={cls} value={cls}>{cls}</option>
                ))}
              </select>
            </div>

            {/* Price Range Filter */}
            <div className="filter-group filter-group-wide">
              <label className="filter-label">Цена, ₽</label>
              <div className="price-range">
                <input
                  type="number"
                  placeholder="От"
                  value={filters.priceRange?.min || ''}
                  onChange={(e) => handlePriceChange('min', e.target.value)}
                  className="price-input"
                />
                <span className="price-separator">—</span>
                <input
                  type="number"
                  placeholder="До"
                  value={filters.priceRange?.max || ''}
                  onChange={(e) => handlePriceChange('max', e.target.value)}
                  className="price-input"
                />
              </div>
            </div>
          </div>

          <div className="filters-actions">
            <button onClick={onReset} className="btn btn-secondary btn-small">
              Сбросить
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Catalog Section
const Catalog = ({ onAddToCart }) => {
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    search: '',
    brand: '',
    power: '',
    area: '',
    efficiency: '',
    priceRange: { min: '', max: '' }
  });

  useEffect(() => {
    fetchProducts();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [products, filters]);

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API}/products`);
      setProducts(response.data);
    } catch (error) {
      console.error('Ошибка загрузки товаров:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...products];

    // Search filter
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(product =>
        product.name.toLowerCase().includes(searchTerm) ||
        product.description.toLowerCase().includes(searchTerm) ||
        product.short_description.toLowerCase().includes(searchTerm)
      );
    }

    // Brand filter
    if (filters.brand) {
      filtered = filtered.filter(product => {
        const brandMatch = product.name.match(/^([A-Za-z\s]+)/);
        const productBrand = brandMatch ? brandMatch[1].trim() : 'Другие';
        return productBrand === filters.brand;
      });
    }

    // Power filter
    if (filters.power) {
      filtered = filtered.filter(product => {
        const power = product.specifications?.['Мощность охлаждения'];
        return power && power.includes(filters.power);
      });
    }

    // Area filter
    if (filters.area) {
      filtered = filtered.filter(product => {
        const area = product.specifications?.['Площадь помещения'];
        return area && area.includes(filters.area);
      });
    }

    // Efficiency filter
    if (filters.efficiency) {
      filtered = filtered.filter(product => {
        const efficiency = product.specifications?.['Класс энергоэффективности'];
        return efficiency === filters.efficiency;
      });
    }

    // Price range filter
    if (filters.priceRange.min || filters.priceRange.max) {
      filtered = filtered.filter(product => {
        const price = product.price;
        const min = filters.priceRange.min ? parseFloat(filters.priceRange.min) : 0;
        const max = filters.priceRange.max ? parseFloat(filters.priceRange.max) : Infinity;
        return price >= min && price <= max;
      });
    }

    setFilteredProducts(filtered);
  };

  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
  };

  const handleResetFilters = () => {
    setFilters({
      search: '',
      brand: '',
      power: '',
      area: '',
      efficiency: '',
      priceRange: { min: '', max: '' }
    });
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Загрузка каталога...</p>
      </div>
    );
  }

  return (
    <div className="section">
      <div className="section-content">
        <ProductFilters
          products={products}
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onReset={handleResetFilters}
        />
        
        <div className="products-header">
          <h2 className="products-title">
            {filteredProducts.length === products.length 
              ? `Все товары (${products.length})`
              : `Найдено: ${filteredProducts.length} из ${products.length}`
            }
          </h2>
        </div>

        {filteredProducts.length === 0 ? (
          <div className="no-results">
            <div className="no-results-icon">🔍</div>
            <h3 className="no-results-title">Товары не найдены</h3>
            <p className="no-results-text">
              Попробуйте изменить параметры поиска или сбросить фильтры
            </p>
            <button onClick={handleResetFilters} className="btn btn-primary">
              Сбросить фильтры
            </button>
          </div>
        ) : (
          <div className="products-grid">
            {filteredProducts.map(product => (
              <ProductCard
                key={product.id}
                product={product}
                onViewDetails={setSelectedProduct}
                onAddToCart={onAddToCart}
              />
            ))}
          </div>
        )}
      </div>
      <ProductDetailsModal
        product={selectedProduct}
        onClose={() => setSelectedProduct(null)}
        onAddToCart={onAddToCart}
      />
    </div>
  );
};

// About Section
const About = () => {
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(0);
  const [currentImage, setCurrentImage] = useState(0);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await axios.get(`${API}/projects`);
      setProjects(response.data);
    } catch (error) {
      console.error('Ошибка загрузки проектов:', error);
    }
  };

  const nextImage = () => {
    if (projects[currentProject]) {
      setCurrentImage((prev) => 
        prev < projects[currentProject].images.length - 1 ? prev + 1 : 0
      );
    }
  };

  const prevImage = () => {
    if (projects[currentProject]) {
      setCurrentImage((prev) => 
        prev > 0 ? prev - 1 : projects[currentProject].images.length - 1
      );
    }
  };

  const nextProject = () => {
    setCurrentProject((prev) => prev < projects.length - 1 ? prev + 1 : 0);
    setCurrentImage(0);
  };

  const prevProject = () => {
    setCurrentProject((prev) => prev > 0 ? prev - 1 : projects.length - 1);
    setCurrentImage(0);
  };

  if (projects.length === 0) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Загрузка проектов...</p>
      </div>
    );
  }

  const project = projects[currentProject];

  return (
    <div className="section">
      <div className="section-content">
        <div className="project-card">
          <div className="project-gallery">
            <div className="gallery-container">
              <img 
                src={project.images[currentImage]} 
                alt={project.title}
                className="gallery-image"
              />
              {project.images.length > 1 && (
                <>
                  <button onClick={prevImage} className="gallery-nav gallery-prev">‹</button>
                  <button onClick={nextImage} className="gallery-nav gallery-next">›</button>
                  <div className="gallery-dots">
                    {project.images.map((_, index) => (
                      <button
                        key={index}
                        onClick={() => setCurrentImage(index)}
                        className={`gallery-dot ${index === currentImage ? 'active' : ''}`}
                      />
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
          
          <div className="project-info">
            <h2 className="project-title">{project.title}</h2>
            <p className="project-description">{project.description}</p>
            <div className="project-address">
              <span className="address-icon">📍</span>
              <span>{project.address}</span>
            </div>
          </div>
        </div>
        
        {projects.length > 1 && (
          <div className="project-navigation">
            <button onClick={prevProject} className="btn btn-secondary">
              ← Предыдущий
            </button>
            <span className="project-indicator">
              {currentProject + 1} из {projects.length}
            </span>
            <button onClick={nextProject} className="btn btn-secondary">
              Следующий →
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// Feedback Section
const Feedback = () => {
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      await axios.post(`${API}/feedback`, formData);
      setFormData({ name: '', phone: '', message: '' });
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 5000);
    } catch (error) {
      console.error('Ошибка отправки формы:', error);
      alert('Ошибка отправки формы. Попробуйте еще раз.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="section">
      <div className="section-content">
        {showSuccess && (
          <div className="alert alert-success">
            <span className="alert-icon">✅</span>
            <span>Ваша заявка отправлена. Мы свяжемся с вами в ближайшее время.</span>
          </div>
        )}
        
        <div className="form-card">
          <h2 className="form-title">Связаться с нами</h2>
          <form onSubmit={handleSubmit} className="contact-form">
            <div className="form-group">
              <label className="form-label">Ваше имя</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="form-input"
                placeholder="Введите ваше имя"
              />
            </div>
            
            <div className="form-group">
              <label className="form-label">Номер телефона</label>
              <input
                type="tel"
                required
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="form-input"
                placeholder="+7 (000) 000-00-00"
              />
            </div>
            
            <div className="form-group">
              <label className="form-label">Сообщение</label>
              <textarea
                required
                rows="4"
                value={formData.message}
                onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                className="form-input form-textarea"
                placeholder="Опишите ваш запрос..."
              />
            </div>
            
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn btn-primary btn-large"
            >
              {isSubmitting ? 'Отправляем...' : 'Отправить заявку'}
            </button>
          </form>
          
          <div className="contact-info">
            <div className="contact-item">
              <span className="contact-icon">📞</span>
              <span>+7 (495) 123-45-67</span>
            </div>
            <div className="contact-item">
              <span className="contact-icon">📧</span>
              <span>info@klimattehno.ru</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Cart Section
const Cart = ({ cartItems, onRemoveItem, onUpdateQuantity, onClearCart }) => {
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [isOrdering, setIsOrdering] = useState(false);

  const totalAmount = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  const handleOrder = async () => {
    setIsOrdering(true);
    try {
      await axios.post(`${API}/orders`, { items: cartItems });
      setShowConfirmation(false);
      onClearCart();
      alert('Спасибо за заказ! Мы свяжемся с вами для подтверждения.');
    } catch (error) {
      console.error('Ошибка оформления заказа:', error);
      alert('Ошибка оформления заказа. Попробуйте еще раз.');
    } finally {
      setIsOrdering(false);
    }
  };

  if (cartItems.length === 0) {
    return (
      <div className="section">
        <div className="section-content">
          <div className="empty-cart">
            <div className="empty-cart-icon">🛒</div>
            <h2 className="empty-cart-title">Корзина пуста</h2>
            <p className="empty-cart-text">Добавьте товары из каталога</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="section">
      <div className="section-content">
        <div className="cart-items">
          {cartItems.map(item => (
            <div key={item.id} className="cart-item">
              <div className="cart-item-info">
                <h3 className="cart-item-name">{item.product_name}</h3>
                <p className="cart-item-price">{item.price.toLocaleString()} ₽ за шт.</p>
              </div>
              <div className="cart-item-controls">
                <div className="quantity-controls">
                  <button
                    onClick={() => onUpdateQuantity(item.id, Math.max(1, item.quantity - 1))}
                    className="quantity-btn"
                  >
                    −
                  </button>
                  <span className="quantity-value">{item.quantity}</span>
                  <button
                    onClick={() => onUpdateQuantity(item.id, item.quantity + 1)}
                    className="quantity-btn"
                  >
                    +
                  </button>
                </div>
                <div className="cart-item-total">
                  {(item.price * item.quantity).toLocaleString()} ₽
                </div>
                <button
                  onClick={() => onRemoveItem(item.id)}
                  className="remove-btn"
                  title="Удалить товар"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
        
        <div className="cart-summary">
          <div className="cart-total">
            <span className="total-label">Итого:</span>
            <span className="total-amount">{totalAmount.toLocaleString()} ₽</span>
          </div>
          <button
            onClick={() => setShowConfirmation(true)}
            className="btn btn-primary btn-large"
          >
            Оформить заказ
          </button>
        </div>
      </div>

      {/* Order Confirmation Modal */}
      {showConfirmation && (
        <div className="modal-overlay" onClick={() => setShowConfirmation(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Подтверждение заказа</h2>
            </div>
            <div className="modal-content">
              <p className="confirmation-text">Подтвердить заказ на сумму {totalAmount.toLocaleString()} ₽?</p>
              
              <div className="order-items">
                {cartItems.map(item => (
                  <div key={item.id} className="order-item">
                    <span className="order-item-name">{item.product_name} × {item.quantity}</span>
                    <span className="order-item-price">{(item.price * item.quantity).toLocaleString()} ₽</span>
                  </div>
                ))}
              </div>
              
              <div className="modal-actions">
                <button
                  onClick={() => setShowConfirmation(false)}
                  className="btn btn-secondary"
                  disabled={isOrdering}
                >
                  Отмена
                </button>
                <button
                  onClick={handleOrder}
                  disabled={isOrdering}
                  className="btn btn-primary"
                >
                  {isOrdering ? 'Оформляем...' : 'Подтвердить'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component
function App() {
  const [activeSection, setActiveSection] = useState('catalog');
  const [cartItems, setCartItems] = useState([]);
  const [telegramWebApp, setTelegramWebApp] = useState(null);
  const [telegramUser, setTelegramUser] = useState(null);

  // Helper function to get user ID with fallback
  const getUserId = () => {
    return telegramUser?.id || 'guest_user';
  };

  useEffect(() => {
    // Initialize Telegram Web App
    const tg = initTelegramWebApp();
    setTelegramWebApp(tg);
    
    const user = getTelegramUser();
    setTelegramUser(user);
    
    console.log('Telegram User:', user);
    
    // initializeData(); // Убираем автоматическую инициализацию
  }, []);

  // Load cart items when telegramUser is available
  useEffect(() => {
    if (telegramUser !== null) {
      fetchCartItems();
    }
  }, [telegramUser]);

  const initializeData = async () => {
    // Функция отключена - данные инициализируются вручную
    console.log('Автоматическая инициализация данных отключена');
    return;
    try {
      await axios.post(`${API}/init-data`);
    } catch (error) {
      console.error('Ошибка инициализации данных:', error);
    }
  };

  const fetchCartItems = async () => {
    try {
      const userId = getUserId();
      const response = await axios.get(`${API}/cart?user_id=${userId}`);
      setCartItems(response.data);
    } catch (error) {
      console.error('Ошибка загрузки корзины:', error);
    }
  };

  const handleAddToCart = async (product) => {
    try {
      const userId = getUserId();
      
      await axios.post(`${API}/cart`, {
        user_id: userId,
        product_id: product.id,
        quantity: 1
      });
      fetchCartItems();
      
      // Добавляем haptic feedback для Telegram
      if (telegramWebApp?.HapticFeedback) {
        telegramWebApp.HapticFeedback.impactOccurred('light');
      }
      
      // Показываем уведомление
      const notification = document.createElement('div');
      notification.className = 'toast-notification';
      notification.textContent = 'Товар добавлен в корзину!';
      document.body.appendChild(notification);
      
      setTimeout(() => {
        notification.classList.add('show');
      }, 100);
      
      setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => document.body.removeChild(notification), 300);
      }, 2000);
      
    } catch (error) {
      console.error('Ошибка добавления в корзину:', error);
      alert('Ошибка добавления товара в корзину');
    }
  };

  const handleRemoveFromCart = async (itemId) => {
    try {
      const userId = getUserId();
      await axios.delete(`${API}/cart/${itemId}?user_id=${userId}`);
      fetchCartItems();
    } catch (error) {
      console.error('Ошибка удаления из корзины:', error);
    }
  };

  const handleUpdateQuantity = async (itemId, newQuantity) => {
    try {
      // Get user_id from telegram or use fallback
      const userId = telegramUser?.id || 'guest_user';
      
      const item = cartItems.find(item => item.id === itemId);
      if (item) {
        await axios.delete(`${API}/cart/${itemId}?user_id=${userId}`);
        if (newQuantity > 0) {
          await axios.post(`${API}/cart`, {
            user_id: userId,
            product_id: item.product_id,
            quantity: newQuantity
          });
        }
        fetchCartItems();
      }
    } catch (error) {
      console.error('Ошибка обновления количества:', error);
    }
  };

  const handleClearCart = async () => {
    try {
      // Get user_id from telegram or use fallback
      const userId = telegramUser?.id || 'guest_user';
      await axios.delete(`${API}/cart?user_id=${userId}`);
      setCartItems([]);
    } catch (error) {
      console.error('Ошибка очистки корзины:', error);
    }
  };

  const renderSection = () => {
    switch (activeSection) {
      case 'catalog':
        return <Catalog onAddToCart={handleAddToCart} />;
      case 'about':
        return <About />;
      case 'feedback':
        return <Feedback />;
      case 'cart':
        return (
          <Cart 
            cartItems={cartItems}
            onRemoveItem={handleRemoveFromCart}
            onUpdateQuantity={handleUpdateQuantity}
            onClearCart={handleClearCart}
          />
        );
      default:
        return <Catalog onAddToCart={handleAddToCart} />;
    }
  };

  return (
    <div className="app">
      <Header />
      <main className="main-content">
        {renderSection()}
      </main>
      <BottomNavigation 
        activeSection={activeSection} 
        setActiveSection={setActiveSection}
        cartCount={cartItems.length}
      />
    </div>
  );
}

export default App;