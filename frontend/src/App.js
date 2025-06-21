import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Navigation Component
const Navigation = ({ activeSection, setActiveSection, cartCount }) => {
  const menuItems = [
    { id: 'catalog', name: 'Каталог', icon: '🛒' },
    { id: 'about', name: 'О нас', icon: '🏢' },
    { id: 'feedback', name: 'Связаться', icon: '📞' },
    { id: 'cart', name: `Корзина (${cartCount})`, icon: '🛍️' }
  ];

  return (
    <nav className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          <div className="text-2xl font-bold">❄️ КлиматТехно</div>
          <div className="flex space-x-6">
            {menuItems.map(item => (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors duration-200 ${
                  activeSection === item.id 
                    ? 'bg-blue-800 text-white' 
                    : 'hover:bg-blue-500'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
};

// Product Card Component
const ProductCard = ({ product, onViewDetails, onAddToCart }) => {
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow duration-300">
      <img 
        src={product.image_url} 
        alt={product.name}
        className="w-full h-48 object-cover"
      />
      <div className="p-6">
        <h3 className="text-xl font-semibold mb-2">{product.name}</h3>
        <p className="text-gray-600 mb-4">{product.short_description}</p>
        <div className="flex justify-between items-center">
          <span className="text-2xl font-bold text-blue-600">
            {product.price.toLocaleString()} ₽
          </span>
          <div className="space-x-2">
            <button
              onClick={() => onViewDetails(product)}
              className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition-colors"
            >
              Подробнее
            </button>
            <button
              onClick={() => onAddToCart(product)}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
            >
              В корзину
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Product Details Modal
const ProductDetailsModal = ({ product, onClose, onAddToCart }) => {
  if (!product) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-screen overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-3xl font-bold">{product.name}</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl"
            >
              ×
            </button>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <img 
                src={product.image_url} 
                alt={product.name}
                className="w-full h-64 object-cover rounded-lg"
              />
            </div>
            <div>
              <p className="text-gray-700 mb-4">{product.description}</p>
              <div className="text-3xl font-bold text-blue-600 mb-6">
                {product.price.toLocaleString()} ₽
              </div>
              <button
                onClick={() => {
                  onAddToCart(product);
                  onClose();
                }}
                className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors text-lg font-semibold"
              >
                Добавить в корзину
              </button>
            </div>
          </div>
          {product.specifications && Object.keys(product.specifications).length > 0 && (
            <div className="mt-6">
              <h3 className="text-xl font-semibold mb-4">Технические характеристики:</h3>
              <div className="grid md:grid-cols-2 gap-4">
                {Object.entries(product.specifications).map(([key, value]) => (
                  <div key={key} className="flex justify-between p-3 bg-gray-50 rounded">
                    <span className="font-medium">{key}:</span>
                    <span>{value}</span>
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

// Catalog Section
const Catalog = ({ onAddToCart }) => {
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProducts();
  }, []);

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

  if (loading) {
    return <div className="text-center py-8">Загрузка каталога...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold text-center mb-8">Каталог кондиционеров</h1>
      <div className="grid lg:grid-cols-3 md:grid-cols-2 gap-6">
        {products.map(product => (
          <ProductCard
            key={product.id}
            product={product}
            onViewDetails={setSelectedProduct}
            onAddToCart={onAddToCart}
          />
        ))}
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
    return <div className="text-center py-8">Загрузка проектов...</div>;
  }

  const project = projects[currentProject];

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold text-center mb-8">Наши проекты</h1>
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* Image Gallery */}
          <div className="relative">
            <img 
              src={project.images[currentImage]} 
              alt={project.title}
              className="w-full h-96 object-cover"
            />
            {project.images.length > 1 && (
              <>
                <button
                  onClick={prevImage}
                  className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-70"
                >
                  ‹
                </button>
                <button
                  onClick={nextImage}
                  className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-70"
                >
                  ›
                </button>
                <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-2">
                  {project.images.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentImage(index)}
                      className={`w-3 h-3 rounded-full ${
                        index === currentImage ? 'bg-white' : 'bg-gray-400'
                      }`}
                    />
                  ))}
                </div>
              </>
            )}
          </div>
          
          {/* Project Info */}
          <div className="p-6">
            <h2 className="text-2xl font-bold mb-4">{project.title}</h2>
            <p className="text-gray-700 mb-4">{project.description}</p>
            <div className="flex items-center text-gray-600">
              <span className="mr-2">📍</span>
              <span>{project.address}</span>
            </div>
          </div>
        </div>
        
        {/* Project Navigation */}
        {projects.length > 1 && (
          <div className="flex justify-between items-center mt-6">
            <button
              onClick={prevProject}
              className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 transition-colors"
            >
              ← Предыдущий проект
            </button>
            <span className="text-gray-600">
              {currentProject + 1} из {projects.length}
            </span>
            <button
              onClick={nextProject}
              className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 transition-colors"
            >
              Следующий проект →
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
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-8">Связаться с нами</h1>
        
        {showSuccess && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-6">
            Ваша заявка отправлена. Мы свяжемся с вами в ближайшее время.
          </div>
        )}
        
        <div className="bg-white rounded-lg shadow-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ваше имя *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Введите ваше имя"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Номер телефона *
              </label>
              <input
                type="tel"
                required
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="+7 (000) 000-00-00"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Сообщение *
              </label>
              <textarea
                required
                rows="4"
                value={formData.message}
                onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Опишите ваш запрос или вопрос..."
              />
            </div>
            
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? 'Отправляем...' : 'Отправить заявку'}
            </button>
          </form>
        </div>
        
        <div className="mt-8 text-center text-gray-600">
          <p className="mb-2">Или свяжитесь с нами напрямую:</p>
          <p>📞 +7 (495) 123-45-67</p>
          <p>📧 info@klimattehno.ru</p>
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
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center mb-8">Корзина</h1>
        <div className="text-center py-16">
          <div className="text-6xl mb-4">🛒</div>
          <p className="text-xl text-gray-600">Ваша корзина пуста</p>
          <p className="text-gray-500 mt-2">Добавьте товары из каталога</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold text-center mb-8">Корзина</h1>
      
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="p-6">
            {cartItems.map(item => (
              <div key={item.id} className="flex items-center justify-between py-4 border-b last:border-b-0">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{item.product_name}</h3>
                  <p className="text-gray-600">{item.price.toLocaleString()} ₽ за шт.</p>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => onUpdateQuantity(item.id, Math.max(1, item.quantity - 1))}
                      className="bg-gray-200 px-3 py-1 rounded hover:bg-gray-300"
                    >
                      -
                    </button>
                    <span className="px-3 py-1 min-w-[3rem] text-center">{item.quantity}</span>
                    <button
                      onClick={() => onUpdateQuantity(item.id, item.quantity + 1)}
                      className="bg-gray-200 px-3 py-1 rounded hover:bg-gray-300"
                    >
                      +
                    </button>
                  </div>
                  <div className="font-bold text-lg min-w-[6rem] text-right">
                    {(item.price * item.quantity).toLocaleString()} ₽
                  </div>
                  <button
                    onClick={() => onRemoveItem(item.id)}
                    className="text-red-500 hover:text-red-700 p-2"
                    title="Удалить товар"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
          
          <div className="bg-gray-50 p-6">
            <div className="flex justify-between items-center mb-4">
              <span className="text-xl font-semibold">Итого:</span>
              <span className="text-2xl font-bold text-blue-600">
                {totalAmount.toLocaleString()} ₽
              </span>
            </div>
            <button
              onClick={() => setShowConfirmation(true)}
              className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors text-lg font-semibold"
            >
              Оформить заказ
            </button>
          </div>
        </div>
      </div>

      {/* Order Confirmation Modal */}
      {showConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-screen overflow-y-auto">
            <div className="p-6">
              <h2 className="text-2xl font-bold mb-4">Подтверждение заказа</h2>
              <p className="mb-4">Вы действительно хотите оформить этот заказ?</p>
              
              <div className="mb-6">
                <h3 className="font-semibold mb-2">Товары в заказе:</h3>
                {cartItems.map(item => (
                  <div key={item.id} className="flex justify-between py-2 border-b">
                    <span>{item.product_name} × {item.quantity}</span>
                    <span>{(item.price * item.quantity).toLocaleString()} ₽</span>
                  </div>
                ))}
                <div className="flex justify-between py-2 font-bold text-lg mt-2">
                  <span>Итого:</span>
                  <span>{totalAmount.toLocaleString()} ₽</span>
                </div>
              </div>
              
              <div className="flex space-x-4">
                <button
                  onClick={() => setShowConfirmation(false)}
                  className="flex-1 bg-gray-500 text-white py-2 rounded hover:bg-gray-600 transition-colors"
                  disabled={isOrdering}
                >
                  Отмена
                </button>
                <button
                  onClick={handleOrder}
                  disabled={isOrdering}
                  className="flex-1 bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition-colors disabled:opacity-50"
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

  useEffect(() => {
    fetchCartItems();
    initializeData();
  }, []);

  const initializeData = async () => {
    try {
      await axios.post(`${API}/init-data`);
    } catch (error) {
      console.error('Ошибка инициализации данных:', error);
    }
  };

  const fetchCartItems = async () => {
    try {
      const response = await axios.get(`${API}/cart`);
      setCartItems(response.data);
    } catch (error) {
      console.error('Ошибка загрузки корзины:', error);
    }
  };

  const handleAddToCart = async (product) => {
    try {
      await axios.post(`${API}/cart`, {
        product_id: product.id,
        quantity: 1
      });
      fetchCartItems();
      alert('Товар добавлен в корзину!');
    } catch (error) {
      console.error('Ошибка добавления в корзину:', error);
      alert('Ошибка добавления товара в корзину');
    }
  };

  const handleRemoveFromCart = async (itemId) => {
    try {
      await axios.delete(`${API}/cart/${itemId}`);
      fetchCartItems();
    } catch (error) {
      console.error('Ошибка удаления из корзины:', error);
    }
  };

  const handleUpdateQuantity = async (itemId, newQuantity) => {
    // For simplicity, remove and re-add with new quantity
    try {
      const item = cartItems.find(item => item.id === itemId);
      if (item) {
        await axios.delete(`${API}/cart/${itemId}`);
        if (newQuantity > 0) {
          await axios.post(`${API}/cart`, {
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
      await axios.delete(`${API}/cart`);
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
    <div className="min-h-screen bg-gray-100">
      <Navigation 
        activeSection={activeSection} 
        setActiveSection={setActiveSection}
        cartCount={cartItems.length}
      />
      {renderSection()}
    </div>
  );
}

export default App;