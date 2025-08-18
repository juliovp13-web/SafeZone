import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Alert, AlertDescription } from './components/ui/alert';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { toast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';
import { 
  Shield, 
  MapPin, 
  Bell, 
  Users, 
  BarChart3, 
  User, 
  Eye, 
  AlertTriangle,
  LogOut,
  ArrowLeft,
  CreditCard,
  QrCode,
  FileBarChart,
  Globe,
  Home,
  Phone
} from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Translation strings
const translations = {
  pt: {
    appName: "SafeZone",
    appTagline: "Segurança comunitária em suas mãos",
    email: "E-mail",
    password: "Senha",
    login: "Entrar",
    register: "Cadastrar",
    price: "Somente R$ 30/mês",
    priceDesc: "Proteja sua casa e toda a vizinhança com tecnologia de ponta",
    invasion: "INVASÃO",
    robbery: "ROUBO", 
    emergency: "EMERGÊNCIA",
    recentAlerts: "Alertas Recentes",
    stopAlerts: "PARAR ALERTAS",
    sendingAlerts: "Enviando alertas contínuos...",
    paymentTitle: "Seu primeiro mês é grátis!",
    paymentDesc: "Após 30 dias, será cobrado R$30/mês automaticamente",
    confirmSubscription: "Confirmar Assinatura",
    creditCard: "Cartão de Crédito/Débito",
    pix: "PIX",
    boleto: "Boleto Bancário"
  },
  en: {
    appName: "SafeZone", 
    appTagline: "Community security in your hands",
    email: "Email",
    password: "Password",
    login: "Login",
    register: "Register",
    price: "Only $5.50/month",
    priceDesc: "Protect your home and neighborhood with cutting-edge technology",
    invasion: "BREAK-IN",
    robbery: "ROBBERY",
    emergency: "EMERGENCY",
    recentAlerts: "Recent Alerts",
    stopAlerts: "STOP ALERTS",
    sendingAlerts: "Sending continuous alerts...",
    paymentTitle: "Your first month is free!",
    paymentDesc: "After 30 days, $5.50/month will be charged automatically",
    confirmSubscription: "Confirm Subscription",
    creditCard: "Credit/Debit Card",
    pix: "PIX",
    boleto: "Bank Slip"
  },
  es: {
    appName: "SafeZone",
    appTagline: "Seguridad comunitaria en tus manos",
    email: "Correo electrónico",
    password: "Contraseña",
    login: "Iniciar sesión",
    register: "Registrarse",
    price: "Solo $30/mes",
    priceDesc: "Protege tu hogar y todo el vecindario con tecnología de punta",
    invasion: "INVASIÓN",
    robbery: "ROBO",
    emergency: "EMERGENCIA", 
    recentAlerts: "Alertas Recientes",
    stopAlerts: "DETENER ALERTAS",
    sendingAlerts: "Enviando alertas continuas...",
    paymentTitle: "¡Tu primer mes es gratis!",
    paymentDesc: "Después de 30 días, se cobrará $30/mes automáticamente",
    confirmSubscription: "Confirmar Suscripción",
    creditCard: "Tarjeta de Crédito/Débito",
    pix: "PIX",
    boleto: "Boleto Bancario"
  }
};

function App() {
  const [currentScreen, setCurrentScreen] = useState('login');
  const [currentLanguage, setCurrentLanguage] = useState('pt');
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [alerts, setAlerts] = useState([]);
  const [activeAlert, setActiveAlert] = useState(null);
  const [alertInterval, setAlertInterval] = useState(null);
  const [languageDropdownOpen, setLanguageDropdownOpen] = useState(false);
  
  // Subscription status states
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [isBlocked, setIsBlocked] = useState(false);
  
  // Form states
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [registerForm, setRegisterForm] = useState({
    name: '', email: '', password: '', state: '', city: '', neighborhood: '', 
    street: '', number: '', residentsCount: 1, residentNames: ['']
  });
  const [paymentForm, setPaymentForm] = useState({
    paymentMethod: 'credit-card',
    cardNumber: '', cardName: '', cardExpiry: '', cardCvv: ''
  });

  const t = translations[currentLanguage];

  // Authentication check on load
  useEffect(() => {
    if (token) {
      fetchProfile();
    }
  }, [token]);

  // Check subscription status periodically
  useEffect(() => {
    if (token && user) {
      checkSubscriptionStatus();
      // Check every 30 minutes
      const interval = setInterval(checkSubscriptionStatus, 30 * 60 * 1000);
      return () => clearInterval(interval);
    }
  }, [token, user]);

  // Fetch user profile
  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API}/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
      
      // Redirect admin to dashboard, regular users to main
      if (response.data.is_admin) {
        setCurrentScreen('admin-dashboard');
      } else {
        setCurrentScreen('main');
        fetchAlerts();
      }
    } catch (error) {
      console.error('Profile fetch failed:', error);
      localStorage.removeItem('token');
      setToken(null);
    }
  };

  // Check subscription status
  const checkSubscriptionStatus = async () => {
    try {
      const response = await axios.get(`${API}/subscription-status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const status = response.data;
      setSubscriptionStatus(status);
      setIsBlocked(status.is_blocked);
      
      // If user is blocked, force to payment screen
      if (status.is_blocked && currentScreen !== 'payment') {
        setCurrentScreen('payment');
        toast({
          title: "Assinatura Vencida",
          description: status.message,
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Failed to check subscription status:', error);
      // If can't check status, assume blocked for safety
      setIsBlocked(true);
      if (currentScreen !== 'payment' && currentScreen !== 'login' && currentScreen !== 'register') {
        setCurrentScreen('payment');
      }
    }
  };

  // Confirm payment and reactivate subscription
  const confirmPayment = async () => {
    try {
      if (!subscriptionStatus) {
        toast({
          title: "Erro",
          description: "Status da assinatura não encontrado",
          variant: "destructive"
        });
        return;
      }

      const response = await axios.post(`${API}/confirm-payment`, {
        subscription_id: subscriptionStatus.subscription_id || 'temp',
        payment_method: paymentForm.paymentMethod,
        transaction_id: 'manual_confirmation_' + Date.now()
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast({
        title: "Pagamento Confirmado!",
        description: response.data.message
      });
      
      // Refresh subscription status
      await checkSubscriptionStatus();
      
      // Return to main screen if no longer blocked
      if (!isBlocked) {
        setCurrentScreen('main');
      }
    } catch (error) {
      toast({
        title: "Erro no pagamento",
        description: error.response?.data?.detail || "Erro interno do servidor",
        variant: "destructive"
      });
    }
  };

  // Fetch alerts
  const fetchAlerts = async () => {
    try {
      const response = await axios.get(`${API}/alerts`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAlerts(response.data);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    }
  };

  // Handle login
  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/login`, loginForm);
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      
      // Check if user is admin and redirect accordingly
      if (userData.is_admin) {
        setCurrentScreen('admin-dashboard');
        toast({
          title: "Login Admin realizado com sucesso!",
          description: `Bem-vindo ao painel administrativo, ${userData.name}!`
        });
      } else {
        setCurrentScreen('main');
        toast({
          title: "Login realizado com sucesso!",
          description: `Bem-vindo, ${userData.name}!`
        });
        fetchAlerts();
      }
      
    } catch (error) {
      toast({
        title: "Erro no login",
        description: error.response?.data?.detail || "Email ou senha incorretos",
        variant: "destructive"
      });
    }
  };

  // Handle registration
  const handleRegistration = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/register`, {
        name: registerForm.name,
        email: registerForm.email,
        password: registerForm.password,
        state: registerForm.state,
        city: registerForm.city,
        neighborhood: registerForm.neighborhood,
        street: registerForm.street,
        number: registerForm.number,
        resident_names: registerForm.residentNames.filter(name => name.trim())
      });
      
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      setCurrentScreen('payment');
      
      toast({
        title: "Cadastro realizado com sucesso!",
        description: "Agora escolha sua forma de pagamento"
      });
      
    } catch (error) {
      toast({
        title: "Erro no cadastro",
        description: error.response?.data?.detail || "Erro ao criar conta",
        variant: "destructive"
      });
    }
  };

  // Handle payment confirmation
  const handlePaymentConfirmation = async () => {
    try {
      const response = await axios.post(`${API}/create-subscription`, paymentForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast({
        title: "Assinatura confirmada!",
        description: response.data.message
      });
      
      setCurrentScreen('main');
      fetchAlerts();
    } catch (error) {
      toast({
        title: "Erro no pagamento",
        description: error.response?.data?.detail || "Erro ao processar pagamento",
        variant: "destructive"
      });
    }
  };

  // Send alert
  const sendAlert = async (type) => {
    try {
      const response = await axios.post(`${API}/alerts`, { type }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const alert = {
        type,
        user_name: user.resident_names[0] || user.name,
        street: user.street,
        number: user.number,
        neighborhood: user.neighborhood,
        timestamp: new Date().toLocaleString()
      };
      
      setActiveAlert(alert);
      setCurrentScreen('alert');
      
      // Start continuous alerts
      const interval = setInterval(() => {
        console.log(`Sending ${type} alert...`);
      }, 5000);
      setAlertInterval(interval);
      
      toast({
        title: `Alerta de ${type} enviado!`,
        description: "Vizinhos estão sendo notificados"
      });
      
    } catch (error) {
      toast({
        title: "Erro ao enviar alerta",  
        description: error.response?.data?.detail || "Erro ao enviar alerta",
        variant: "destructive"
      });
    }
  };

  // Stop alert
  const stopAlert = () => {
    if (alertInterval) {
      clearInterval(alertInterval);
      setAlertInterval(null);
    }
    setActiveAlert(null);
    setCurrentScreen('main');
    fetchAlerts();
  };

  // Handle logout
  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setCurrentScreen('login');
    setAlerts([]);
  };

  // Update residents fields
  const updateResidentsFields = (count) => {
    const newNames = Array(count).fill('').map((_, i) => registerForm.residentNames[i] || '');
    setRegisterForm(prev => ({ ...prev, residentsCount: count, residentNames: newNames }));
  };

  // Render Language Selector
  const LanguageSelector = () => (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setLanguageDropdownOpen(!languageDropdownOpen)}
        className="text-xl p-2"
      >
        <Globe className="w-5 h-5" />
      </Button>
      {languageDropdownOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg z-50 border">
          <div className="py-1">
            {[
              { code: 'pt', label: '🇧🇷 Português' },
              { code: 'en', label: '🇺🇸 English' },
              { code: 'es', label: '🇪🇸 Español' }
            ].map((lang) => (
              <button
                key={lang.code}
                className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center"
                onClick={() => {
                  setCurrentLanguage(lang.code);
                  setLanguageDropdownOpen(false);
                }}
              >
                {lang.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // Login Screen
  if (currentScreen === 'login') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="max-w-md mx-auto pt-8 px-6">
          <div className="flex justify-end mb-4">
            <LanguageSelector />
          </div>
          
          <div className="text-center mb-8">
            <div className="flex items-center justify-center mb-4">
              <Shield className="w-12 h-12 text-blue-600 mr-2" />
              <h1 className="text-4xl font-bold text-blue-800">{t.appName}</h1>
            </div>
            <p className="text-gray-600">{t.appTagline}</p>
          </div>

          <Card className="mb-6">
            <CardContent className="p-6">
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <Label htmlFor="email">{t.email}</Label>
                  <Input
                    id="email"
                    type="email"
                    value={loginForm.email}
                    onChange={(e) => setLoginForm(prev => ({ ...prev, email: e.target.value }))}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="password">{t.password}</Label>
                  <Input
                    id="password"
                    type="password"
                    value={loginForm.password}
                    onChange={(e) => setLoginForm(prev => ({ ...prev, password: e.target.value }))}
                    required
                  />
                </div>
                <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700">
                  {t.login}
                </Button>
              </form>
              <Button 
                variant="outline" 
                className="w-full mt-3"
                onClick={() => setCurrentScreen('register')}
              >
                {t.register}
              </Button>
              <Button 
                variant="outline" 
                className="w-full mt-2 border-orange-300 text-orange-600 hover:bg-orange-50"
                onClick={() => setCurrentScreen('admin-login')}
              >
                🔐 Login Admin
              </Button>
            </CardContent>
          </Card>

          {/* Pricing Card */}
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="p-6">
              <p className="text-center font-bold text-blue-800 mb-2">{t.price}</p>
              <p className="text-center text-sm text-gray-600 mb-4">{t.priceDesc}</p>
              
              <div className="space-y-3 text-sm">
                <div className="flex items-start">
                  <Shield className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                  <span>Alertas instantâneos de invasão, roubo ou emergência</span>
                </div>
                <div className="flex items-start">
                  <MapPin className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                  <span>Localização exata da ocorrência no mapa</span>
                </div>
                <div className="flex items-start">
                  <Bell className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                  <span>Notificações em tela cheia para máxima atenção</span>
                </div>
                <div className="flex items-start">
                  <Users className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                  <span>Rede de vizinhos unidos pela segurança</span>
                </div>
                <div className="flex items-start">
                  <BarChart3 className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                  <span>Histórico de alertas para acompanhamento</span>
                </div>
              </div>
              
              <p className="text-xs text-gray-500 mt-4 text-center">
                💬 Ajude-nos a manter o melhor aplicativo de segurança já criado. Sua assinatura mantém a tecnologia ativa e protege toda a comunidade.
              </p>
            </CardContent>
          </Card>
        </div>
        <Toaster />
      </div>
    );
  }

  // Register Screen
  if (currentScreen === 'register') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="max-w-md mx-auto pt-8 px-6">
          <div className="flex items-center mb-6">
            <Button variant="ghost" onClick={() => setCurrentScreen('login')} className="mr-4">
              <ArrowLeft className="w-4 h-4" />
            </Button>
            <h2 className="text-2xl font-bold text-blue-800">Cadastro</h2>
          </div>

          <Card>
            <CardContent className="p-6">
              <form onSubmit={handleRegistration} className="space-y-4">
                <div>
                  <Label htmlFor="reg-name">Nome Completo</Label>
                  <Input
                    id="reg-name"
                    value={registerForm.name}
                    onChange={(e) => setRegisterForm(prev => ({ ...prev, name: e.target.value }))}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="reg-email">{t.email}</Label>
                  <Input
                    id="reg-email"
                    type="email"
                    value={registerForm.email}
                    onChange={(e) => setRegisterForm(prev => ({ ...prev, email: e.target.value }))}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="reg-password">{t.password}</Label>
                  <Input
                    id="reg-password"
                    type="password"
                    value={registerForm.password}
                    onChange={(e) => setRegisterForm(prev => ({ ...prev, password: e.target.value }))}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="reg-state">Estado</Label>
                  <Input
                    id="reg-state"
                    value={registerForm.state}
                    onChange={(e) => setRegisterForm(prev => ({ ...prev, state: e.target.value }))}
                    placeholder="Ex: SP, RJ, MG"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="reg-city">Cidade</Label>
                  <Input
                    id="reg-city"
                    value={registerForm.city}
                    onChange={(e) => setRegisterForm(prev => ({ ...prev, city: e.target.value }))}
                    placeholder="Ex: São Paulo, Rio de Janeiro"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="reg-neighborhood">Bairro</Label>
                  <Input
                    id="reg-neighborhood"
                    value={registerForm.neighborhood}
                    onChange={(e) => setRegisterForm(prev => ({ ...prev, neighborhood: e.target.value }))}
                    placeholder="Ex: Vila Olímpia, Copacabana"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="reg-street">Rua</Label>
                  <Input
                    id="reg-street"
                    value={registerForm.street}
                    onChange={(e) => setRegisterForm(prev => ({ ...prev, street: e.target.value }))}
                    placeholder="Ex: Rua das Flores, Av. Paulista"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="reg-number">Número</Label>
                  <Input
                    id="reg-number"
                    value={registerForm.number}
                    onChange={(e) => setRegisterForm(prev => ({ ...prev, number: e.target.value }))}
                    placeholder="Ex: 123, 456-A"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="reg-neighborhood">Bairro</Label>
                  <Input
                    id="reg-neighborhood"
                    value={registerForm.neighborhood}
                    onChange={(e) => setRegisterForm(prev => ({ ...prev, neighborhood: e.target.value }))}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="residents-count">Número de residentes</Label>
                  <Input
                    id="residents-count"
                    type="number"
                    min="1"
                    value={registerForm.residentsCount}
                    onChange={(e) => updateResidentsFields(parseInt(e.target.value) || 1)}
                    required
                  />
                </div>
                
                {/* Resident names */}
                {Array.from({ length: registerForm.residentsCount }, (_, i) => (
                  <div key={i}>
                    <Label htmlFor={`resident-name-${i + 1}`}>Nome do residente {i + 1}</Label>
                    <Input
                      id={`resident-name-${i + 1}`}
                      value={registerForm.residentNames[i] || ''}
                      onChange={(e) => {
                        const newNames = [...registerForm.residentNames];
                        newNames[i] = e.target.value;
                        setRegisterForm(prev => ({ ...prev, residentNames: newNames }));
                      }}
                      required
                    />
                  </div>
                ))}
                
                <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700">
                  Completar Cadastro
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
        <Toaster />
      </div>
    );
  }

  // Payment Screen
  if (currentScreen === 'payment') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="max-w-md mx-auto pt-8 px-6">
          <div className="flex items-center mb-6">
            <Button variant="ghost" onClick={() => setCurrentScreen('register')} className="mr-4">
              <ArrowLeft className="w-4 h-4" />
            </Button>
            <h2 className="text-2xl font-bold text-blue-800">Forma de Pagamento</h2>
          </div>

          <div className="text-center mb-6">
            <p className="text-lg font-semibold">{t.paymentTitle}</p>
            <p className="text-sm text-gray-600">{t.paymentDesc}</p>
          </div>

          <Card className="mb-6">
            <CardContent className="p-6 space-y-4">
              {/* Payment method selection */}
              <div className="space-y-3">
                <div className="flex items-center space-x-3 p-3 border rounded-lg cursor-pointer"
                     onClick={() => setPaymentForm(prev => ({ ...prev, paymentMethod: 'credit-card' }))}>
                  <input
                    type="radio"
                    name="payment"
                    checked={paymentForm.paymentMethod === 'credit-card'}
                    onChange={() => setPaymentForm(prev => ({ ...prev, paymentMethod: 'credit-card' }))}
                  />
                  <div className="flex-1">
                    <p className="font-semibold">{t.creditCard}</p>
                    <p className="text-sm text-gray-600">Visa, Mastercard, etc</p>
                  </div>
                  <CreditCard className="w-5 h-5 text-blue-600" />
                </div>

                <div className="flex items-center space-x-3 p-3 border rounded-lg cursor-pointer"
                     onClick={() => setPaymentForm(prev => ({ ...prev, paymentMethod: 'pix' }))}>
                  <input
                    type="radio"
                    name="payment"
                    checked={paymentForm.paymentMethod === 'pix'}
                    onChange={() => setPaymentForm(prev => ({ ...prev, paymentMethod: 'pix' }))}
                  />
                  <div className="flex-1">
                    <p className="font-semibold">{t.pix}</p>
                    <p className="text-sm text-gray-600">Pagamento instantâneo</p>
                  </div>
                  <QrCode className="w-5 h-5 text-blue-600" />
                </div>

                <div className="flex items-center space-x-3 p-3 border rounded-lg cursor-pointer"
                     onClick={() => setPaymentForm(prev => ({ ...prev, paymentMethod: 'boleto' }))}>
                  <input
                    type="radio"
                    name="payment"
                    checked={paymentForm.paymentMethod === 'boleto'}
                    onChange={() => setPaymentForm(prev => ({ ...prev, paymentMethod: 'boleto' }))}
                  />
                  <div className="flex-1">
                    <p className="font-semibold">{t.boleto}</p>
                    <p className="text-sm text-gray-600">Pagamento em até 2 dias úteis</p>
                  </div>
                  <FileBarChart className="w-5 h-5 text-blue-600" />
                </div>
              </div>

              {/* Credit card fields */}
              {paymentForm.paymentMethod === 'credit-card' && (
                <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
                  <div>
                    <Label htmlFor="card-number">Número do Cartão</Label>
                    <Input
                      id="card-number"
                      placeholder="1234 5678 9012 3456"
                      value={paymentForm.cardNumber}
                      onChange={(e) => setPaymentForm(prev => ({ ...prev, cardNumber: e.target.value }))}
                    />
                  </div>
                  <div>
                    <Label htmlFor="card-name">Nome no Cartão</Label>
                    <Input
                      id="card-name"
                      placeholder="Nome como está no cartão"
                      value={paymentForm.cardName}
                      onChange={(e) => setPaymentForm(prev => ({ ...prev, cardName: e.target.value }))}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="card-expiry">Validade</Label>
                      <Input
                        id="card-expiry"
                        placeholder="MM/AA"
                        value={paymentForm.cardExpiry}
                        onChange={(e) => setPaymentForm(prev => ({ ...prev, cardExpiry: e.target.value }))}
                      />
                    </div>
                    <div>
                      <Label htmlFor="card-cvv">CVV</Label>
                      <Input
                        id="card-cvv"
                        placeholder="123"
                        value={paymentForm.cardCvv}
                        onChange={(e) => setPaymentForm(prev => ({ ...prev, cardCvv: e.target.value }))}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* PIX info */}
              {paymentForm.paymentMethod === 'pix' && (
                <div className="p-4 bg-gray-50 rounded-lg text-center">
                  <QrCode className="w-16 h-16 mx-auto text-blue-600 mb-2" />
                  <p className="font-semibold">Pague com PIX</p>
                  <p className="text-sm text-gray-600 mb-4">Código PIX será gerado após confirmação</p>
                  <p className="text-xs font-mono bg-white p-2 rounded">09b74dd4-64da-4563-b769-95cec83659f0</p>
                </div>
              )}

              {/* Boleto info */}
              {paymentForm.paymentMethod === 'boleto' && (
                <div className="p-4 bg-gray-50 rounded-lg text-center">
                  <FileBarChart className="w-16 h-16 mx-auto text-blue-600 mb-2" />
                  <p className="font-semibold">Boleto Bancário</p>
                  <p className="text-sm text-gray-600 mb-2">O boleto será gerado após a confirmação</p>
                  <p className="text-sm">Vencimento em 2 dias úteis</p>
                </div>
              )}

              <Button onClick={handlePaymentConfirmation} className="w-full bg-blue-600 hover:bg-blue-700">
                {t.confirmSubscription}
              </Button>
            </CardContent>
          </Card>
        </div>
        <Toaster />
      </div>
    );
  }

  // Main App Screen
  if (currentScreen === 'main') {
    return (
      <div className="min-h-screen bg-gray-100">
        {/* Header */}
        <div className="bg-blue-700 text-white p-4 flex justify-between items-center">
          <div className="flex items-center">
            <Shield className="w-6 h-6 mr-2" />
            <h2 className="font-bold text-xl">SafeZone</h2>
          </div>
          <Button variant="ghost" onClick={handleLogout} className="text-white hover:bg-blue-600">
            <LogOut className="w-5 h-5" />
          </Button>
        </div>

        <div className="p-6">
          {/* User Info */}
          <Card className="mb-6">
            <CardContent className="p-4">
              <div className="flex items-center mb-2">
                <Home className="w-5 h-5 text-blue-600 mr-2" />
                <span className="font-semibold">{user?.resident_names?.[0] || user?.name}</span>
              </div>
              <p className="text-sm text-gray-600">{user?.street}, {user?.number}</p>
              <p className="text-sm text-gray-600">{user?.neighborhood}</p>
              <p className="text-sm text-gray-500">{user?.city} - {user?.state}</p>
            </CardContent>
          </Card>

          {/* Emergency Buttons */}
          <div className="grid grid-cols-1 gap-4 mb-8">
            <Button
              onClick={() => sendAlert('invasão')}
              className="h-24 bg-red-600 hover:bg-red-700 text-white text-xl font-bold"
            >
              <div className="flex flex-col items-center">
                <User className="w-8 h-8 mb-2" />
                <span>{t.invasion}</span>
              </div>
            </Button>

            <Button
              onClick={() => sendAlert('roubo')}
              className="h-24 bg-orange-500 hover:bg-orange-600 text-white text-xl font-bold"
            >
              <div className="flex flex-col items-center">
                <Eye className="w-8 h-8 mb-2" />
                <span>{t.robbery}</span>
              </div>
            </Button>

            <Button
              onClick={() => sendAlert('emergência')}
              className="h-24 bg-yellow-500 hover:bg-yellow-600 text-white text-xl font-bold"
            >
              <div className="flex flex-col items-center">
                <AlertTriangle className="w-8 h-8 mb-2" />
                <span>{t.emergency}</span>
              </div>
            </Button>
          </div>

          {/* Recent Alerts */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Bell className="w-5 h-5 mr-2" />
                {t.recentAlerts}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {alerts.length === 0 ? (
                <p className="text-gray-500 text-center py-4">Nenhum alerta recente</p>
              ) : (
                <div className="space-y-3">
                  {alerts.map((alert, index) => (
                    <div key={index} className="flex items-center p-3 border rounded-lg">
                      {alert.type === 'invasão' && <User className="w-5 h-5 text-red-500 mr-3" />}
                      {alert.type === 'roubo' && <Eye className="w-5 h-5 text-orange-500 mr-3" />}
                      {alert.type === 'emergência' && <AlertTriangle className="w-5 h-5 text-yellow-500 mr-3" />}
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <h4 className="font-semibold text-sm">{alert.type.toUpperCase()}</h4>
                          <Badge variant="secondary" className="text-xs">{alert.timestamp}</Badge>
                        </div>
                        <p className="text-xs text-gray-600">{alert.street}, {alert.number}</p>
                        <p className="text-xs text-gray-500">por {alert.user_name}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
        <Toaster />
      </div>
    );
  }

  // Alert Screen
  if (currentScreen === 'alert' && activeAlert) {
    return (
      <div className="fixed inset-0 bg-gray-900 text-white z-50 flex flex-col items-center justify-center p-6 animate-pulse">
        <div className="text-center max-w-md">
          <div className="mb-6">
            {activeAlert.type === 'invasão' && <User className="w-24 h-24 mx-auto text-red-500 animate-bounce" />}
            {activeAlert.type === 'roubo' && <Eye className="w-24 h-24 mx-auto text-orange-500 animate-bounce" />}
            {activeAlert.type === 'emergência' && <AlertTriangle className="w-24 h-24 mx-auto text-yellow-500 animate-bounce" />}
          </div>
          
          <h2 className="text-3xl font-bold mb-2">{activeAlert.user_name}</h2>
          <div className="mb-4 text-xl">
            <p className="font-medium">{activeAlert.street}, {activeAlert.number}</p>
            <p className="font-medium">{activeAlert.neighborhood}</p>
          </div>
          <p className="text-2xl text-red-500 font-bold mb-4">
            {activeAlert.type.toUpperCase()} EM ANDAMENTO!
          </p>
          
          <div className="bg-gray-800 p-4 rounded-lg mb-6">
            <p className="text-lg">{t.sendingAlerts}</p>
          </div>
          
          <Button onClick={stopAlert} className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 text-lg font-bold mb-4">
            {t.stopAlerts}
          </Button>
          
          <p className="text-center text-gray-400 text-sm">Alertas são enviados a cada 5 segundos</p>
        </div>
      </div>
    );
  }

  // Admin Login Screen  
  if (currentScreen === 'admin-login') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-100">
        <div className="max-w-md mx-auto pt-8 px-6">
          <div className="flex items-center mb-6">
            <Button variant="ghost" onClick={() => setCurrentScreen('login')} className="mr-4">
              <ArrowLeft className="w-4 h-4" />
            </Button>
            <h2 className="text-2xl font-bold text-orange-800">🔐 Login Admin</h2>
          </div>

          <Card className="mb-6 border-orange-200">
            <CardContent className="p-6">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Shield className="w-8 h-8 text-orange-600" />
                </div>
                <h3 className="text-lg font-semibold text-orange-800">Painel Administrativo</h3>
                <p className="text-sm text-gray-600">Acesso restrito à equipe de suporte</p>
              </div>

              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <Label htmlFor="admin-email">Email Administrativo</Label>
                  <Input
                    id="admin-email"
                    type="email"
                    value={loginForm.email}
                    onChange={(e) => setLoginForm(prev => ({ ...prev, email: e.target.value }))}
                    placeholder="admin@safezone.com"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="admin-password">Senha</Label>
                  <Input
                    id="admin-password"
                    type="password"
                    value={loginForm.password}
                    onChange={(e) => setLoginForm(prev => ({ ...prev, password: e.target.value }))}
                    required
                  />
                </div>
                <Button type="submit" className="w-full bg-orange-600 hover:bg-orange-700">
                  🔐 Entrar como Admin
                </Button>
              </form>
              
              <div className="mt-4 p-3 bg-orange-50 rounded-lg">
                <p className="text-xs text-orange-700 text-center">
                  ⚡ Acesso ao painel de controle, mensagens de suporte e gerenciamento de usuários
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
        <Toaster />
      </div>
    );
  }

  // Admin Dashboard Screen
  if (currentScreen === 'admin-dashboard') {
    return <AdminDashboard 
      user={user} 
      token={token} 
      handleLogout={handleLogout}
      API={API}
    />;
  }

  return null;
}

// Admin Dashboard Component
function AdminDashboard({ user, token, handleLogout, API }) {
  const [activeTab, setActiveTab] = useState('stats');
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [helpMessages, setHelpMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newAdminEmail, setNewAdminEmail] = useState('');

  // Fetch admin stats
  const fetchStats = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      toast({
        title: "Erro ao carregar estatísticas",
        description: "Não foi possível carregar os dados",
        variant: "destructive"
      });
    }
    setLoading(false);
  };

  // Fetch all users
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
      toast({
        title: "Erro ao carregar usuários",
        description: "Não foi possível carregar os usuários",
        variant: "destructive"
      });
    }
    setLoading(false);
  };

  // Fetch help messages
  const fetchHelpMessages = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/admin/help-messages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHelpMessages(response.data);
    } catch (error) {
      console.error('Failed to fetch help messages:', error);
      toast({
        title: "Erro ao carregar mensagens",
        description: "Não foi possível carregar as mensagens de suporte",
        variant: "destructive"
      });
    }
    setLoading(false);
  };

  // Add new admin
  const addAdmin = async () => {
    if (!newAdminEmail) {
      toast({
        title: "Email obrigatório",
        description: "Digite um email para adicionar como admin",
        variant: "destructive"
      });
      return;
    }

    try {
      await axios.post(`${API}/admin/set-admin`, {
        email: newAdminEmail,
        is_admin: true,
        is_vip: true,
        vip_permanent: true
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast({
        title: "Admin adicionado com sucesso!",
        description: `${newAdminEmail} agora é admin/VIP permanente`
      });
      
      setNewAdminEmail('');
      if (activeTab === 'users') {
        fetchUsers();
      }
    } catch (error) {
      toast({
        title: "Erro ao adicionar admin",
        description: error.response?.data?.detail || "Erro interno do servidor",
        variant: "destructive"
      });
    }
  };

  // Load data when tab changes
  React.useEffect(() => {
    if (activeTab === 'stats') {
      fetchStats();
    } else if (activeTab === 'users') {
      fetchUsers();
    } else if (activeTab === 'support') {
      fetchHelpMessages();
    }
  }, [activeTab]);

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-orange-600 text-white p-4 flex justify-between items-center">
        <div className="flex items-center">
          <Shield className="w-6 h-6 mr-2" />
          <h2 className="font-bold text-xl">SafeZone Admin</h2>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-sm">👋 Olá, {user?.name}</span>
          <Button variant="ghost" onClick={handleLogout} className="text-white hover:bg-orange-700">
            <LogOut className="w-5 h-5" />
          </Button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b">
        <div className="flex space-x-8 px-6">
          {[
            { key: 'stats', label: '📊 Estatísticas', icon: BarChart3 },
            { key: 'users', label: '👥 Usuários', icon: Users },
            { key: 'support', label: '💬 Suporte', icon: Phone },
            { key: 'admins', label: '🔐 Admins', icon: Shield }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`py-4 px-2 border-b-2 font-medium text-sm ${
                activeTab === tab.key
                  ? 'border-orange-500 text-orange-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-2">
                <tab.icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="p-6">
        {/* Statistics Tab */}
        {activeTab === 'stats' && (
          <div className="space-y-6">
            <h3 className="text-2xl font-bold text-gray-900">Estatísticas do Sistema</h3>
            
            {loading ? (
              <div className="text-center">Carregando...</div>
            ) : stats ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <Users className="w-8 h-8 text-blue-600" />
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Total Usuários</p>
                        <p className="text-2xl font-bold text-gray-900">{stats.total_users}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <CreditCard className="w-8 h-8 text-green-600" />
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Assinaturas Ativas</p>
                        <p className="text-2xl font-bold text-gray-900">{stats.active_subscriptions}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <AlertTriangle className="w-8 h-8 text-red-600" />
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Total Alertas</p>
                        <p className="text-2xl font-bold text-gray-900">{stats.total_alerts}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <Phone className="w-8 h-8 text-orange-600" />
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Mensagens Pendentes</p>
                        <p className="text-2xl font-bold text-gray-900">{stats.pending_help_messages}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : null}
          </div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="space-y-6">
            <h3 className="text-2xl font-bold text-gray-900">Gerenciamento de Usuários</h3>
            
            {loading ? (
              <div className="text-center">Carregando usuários...</div>
            ) : (
              <Card>
                <CardContent className="p-6">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Usuário
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Endereço Completo
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Status
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Cadastro
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {users.map((user) => (
                          <tr key={user.id}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">{user.name}</div>
                              <div className="text-sm text-gray-500">{user.email}</div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="text-sm text-gray-900">{user.address}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex space-x-2">
                                {user.is_admin && (
                                  <Badge className="bg-orange-100 text-orange-800">Admin</Badge>
                                )}
                                {user.is_vip && (
                                  <Badge className="bg-purple-100 text-purple-800">VIP</Badge>
                                )}
                                {!user.is_admin && !user.is_vip && (
                                  <Badge variant="secondary">Regular</Badge>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {user.created_at}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Support Messages Tab */}
        {activeTab === 'support' && (
          <div className="space-y-6">
            <h3 className="text-2xl font-bold text-gray-900">Mensagens de Suporte</h3>
            
            {loading ? (
              <div className="text-center">Carregando mensagens...</div>
            ) : (
              <div className="space-y-4">
                {helpMessages.length === 0 ? (
                  <Card>
                    <CardContent className="p-6 text-center">
                      <p className="text-gray-500">Nenhuma mensagem de suporte encontrada</p>
                    </CardContent>
                  </Card>
                ) : (
                  helpMessages.map((message) => (
                    <Card key={message.id}>
                      <CardContent className="p-6">
                        <div className="flex justify-between items-start mb-4">
                          <div>
                            <h4 className="font-semibold text-lg">{message.user_name}</h4>
                            <p className="text-sm text-gray-600">{message.user_email}</p>
                            <p className="text-sm text-blue-600">📍 {message.user_address}</p>
                          </div>
                          <div className="text-right">
                            <Badge 
                              variant={message.status === 'pending' ? 'destructive' : 'default'}
                            >
                              {message.status === 'pending' ? 'Pendente' : 'Resolvido'}
                            </Badge>
                            <p className="text-xs text-gray-500 mt-1">{message.created_at}</p>
                          </div>
                        </div>
                        
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <p className="text-gray-800">{message.message}</p>
                        </div>
                        
                        {message.admin_response && (
                          <div className="mt-4 bg-blue-50 p-4 rounded-lg">
                            <p className="text-sm font-semibold text-blue-800">Resposta do Admin:</p>
                            <p className="text-blue-700">{message.admin_response}</p>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            )}
          </div>
        )}

        {/* Add Admins Tab */}
        {activeTab === 'admins' && (
          <div className="space-y-6">
            <h3 className="text-2xl font-bold text-gray-900">Adicionar Administradores</h3>
            
            <Card>
              <CardContent className="p-6">
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="admin-email">Email do Novo Admin</Label>
                    <div className="flex space-x-2 mt-2">
                      <Input
                        id="admin-email"
                        type="email"
                        value={newAdminEmail}
                        onChange={(e) => setNewAdminEmail(e.target.value)}
                        placeholder="email@exemplo.com"
                        className="flex-1"
                      />
                      <Button onClick={addAdmin} className="bg-orange-600 hover:bg-orange-700">
                        Adicionar Admin
                      </Button>
                    </div>
                  </div>
                  
                  <Alert>
                    <Shield className="w-4 h-4" />
                    <AlertDescription>
                      🎯 <strong>Admins têm acesso total:</strong> Painel de controle, gerenciamento de usuários, 
                      mensagens de suporte e status VIP permanente (não precisam pagar assinatura).
                    </AlertDescription>
                  </Alert>

                  <div className="bg-green-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-green-800 mb-2">✅ Benefícios do Admin/VIP:</h4>
                    <ul className="text-sm text-green-700 space-y-1">
                      <li>• Acesso permanente sem pagamento</li>
                      <li>• Painel administrativo completo</li>
                      <li>• Visualização de todas as mensagens de suporte</li>
                      <li>• Gerenciamento de outros usuários</li>
                      <li>• Estatísticas do sistema em tempo real</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
      <Toaster />
    </div>
  );
}

export default App;