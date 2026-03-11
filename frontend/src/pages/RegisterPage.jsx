/**
 * 用户注册页面
 * 收集生辰八字信息，计算命盘
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Calendar, MapPin, Clock, ChevronRight, ChevronLeft, Eye, EyeOff, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';
import { authService, baziService, userStorage } from '../services/authService';
import { useLanguage } from '../i18n';

// 生成年份选项 (1920-2020)
const YEARS = Array.from({ length: 101 }, (_, i) => 2020 - i);
const MONTHS = Array.from({ length: 12 }, (_, i) => i + 1);
const DAYS = Array.from({ length: 31 }, (_, i) => i + 1);

export default function RegisterPage() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  // 省市数据
  const [provinces, setProvinces] = useState([]);
  const [cities, setCities] = useState([]);
  const [shichenOptions, setShichenOptions] = useState([]);
  
  // 表单数据
  const [formData, setFormData] = useState({
    // 步骤1: 账户信息
    username: '',
    password: '',
    phone: '',
    // 步骤2: 生辰信息
    name: '',
    gender: '男',
    birth_year: 1990,
    birth_month: 1,
    birth_day: 1,
    birth_hour: 'unknown',
    birth_province: '',
    birth_city: '',
  });
  
  // 命盘预览
  const [baziPreview, setBaziPreview] = useState(null);
  
  // 加载省份和时辰数据
  useEffect(() => {
    const loadData = async () => {
      try {
        const [provRes, shichenRes] = await Promise.all([
          baziService.getProvinces(),
          baziService.getShichenOptions(),
        ]);
        setProvinces(provRes.provinces || []);
        setShichenOptions(shichenRes.shichen || []);
      } catch (error) {
        console.error('Failed to load data:', error);
      }
    };
    loadData();
  }, []);
  
  // 加载城市数据
  useEffect(() => {
    const loadCities = async () => {
      if (formData.birth_province) {
        try {
          const res = await baziService.getCities(formData.birth_province);
          setCities(res.cities || []);
          // 自动选择第一个城市
          if (res.cities?.length > 0) {
            setFormData(prev => ({ ...prev, birth_city: res.cities[0] }));
          }
        } catch (error) {
          console.error('Failed to load cities:', error);
        }
      }
    };
    loadCities();
  }, [formData.birth_province]);
  
  // 计算命盘预览
  useEffect(() => {
    const calculatePreview = async () => {
      if (step === 3 && formData.name && formData.birth_year) {
        try {
          const res = await baziService.calculateBazi({
            name: formData.name,
            gender: formData.gender,
            birth_year: formData.birth_year,
            birth_month: formData.birth_month,
            birth_day: formData.birth_day,
            birth_hour: formData.birth_hour,
            birth_province: formData.birth_province,
            birth_city: formData.birth_city,
          });
          if (res.success) {
            setBaziPreview(res.bazi);
          }
        } catch (error) {
          console.error('Failed to calculate bazi preview:', error);
        }
      }
    };
    calculatePreview();
  }, [step, formData]);
  
  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };
  
  const validateStep = (currentStep) => {
    if (currentStep === 1) {
      if (!formData.username || !formData.password) {
        toast.error('请填写用户名和密码');
        return false;
      }
      if (formData.password.length < 6) {
        toast.error('密码至少6位');
        return false;
      }
    } else if (currentStep === 2) {
      if (!formData.name) {
        toast.error('请填写姓名');
        return false;
      }
    }
    return true;
  };
  
  const nextStep = () => {
    if (validateStep(step)) {
      setStep(prev => Math.min(prev + 1, 3));
    }
  };
  
  const prevStep = () => {
    setStep(prev => Math.max(prev - 1, 1));
  };
  
  const handleSubmit = async () => {
    setLoading(true);
    try {
      const res = await authService.register(formData);
      if (res.success) {
        userStorage.setUser(res.user);
        toast.success('注册成功！');
        navigate('/profile');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || '注册失败，请重试');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-[#0a0e17] py-8 px-4">
      {/* 八卦纹路背景 */}
      <div className="fixed inset-0 opacity-5 pointer-events-none">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23f0a500' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }} />
      </div>
      
      <div className="max-w-lg mx-auto relative z-10">
        {/* 标题 */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-[#f0a500] mb-2">命理注册</h1>
          <p className="text-[#a1a1aa]">填写您的生辰信息，开启命理之旅</p>
        </div>
        
        {/* 进度条 */}
        <div className="mb-8">
          <div className="flex justify-between mb-2">
            <span className={`text-sm ${step >= 1 ? 'text-[#f0a500]' : 'text-[#52525b]'}`}>① 账户信息</span>
            <span className={`text-sm ${step >= 2 ? 'text-[#f0a500]' : 'text-[#52525b]'}`}>② 生辰信息</span>
            <span className={`text-sm ${step >= 3 ? 'text-[#f0a500]' : 'text-[#52525b]'}`}>③ 命盘生成</span>
          </div>
          <Progress value={(step / 3) * 100} className="h-2 bg-[#1e2330]" />
        </div>
        
        {/* 步骤1: 账户信息 */}
        {step === 1 && (
          <Card className="bg-[#141824] border-[#f0a500]/30">
            <CardHeader>
              <CardTitle className="text-[#f0a500] flex items-center gap-2">
                <User className="w-5 h-5" />
                账户信息
              </CardTitle>
              <CardDescription className="text-[#a1a1aa]">
                创建您的账户
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label className="text-white">用户名 *</Label>
                <Input
                  value={formData.username}
                  onChange={(e) => handleInputChange('username', e.target.value)}
                  placeholder="请输入用户名"
                  className="bg-[#0a0e17] border-[#2a2f3e] text-white"
                  data-testid="username-input"
                />
              </div>
              
              <div className="space-y-2">
                <Label className="text-white">密码 *</Label>
                <div className="relative">
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    value={formData.password}
                    onChange={(e) => handleInputChange('password', e.target.value)}
                    placeholder="请输入密码（至少6位）"
                    className="bg-[#0a0e17] border-[#2a2f3e] text-white pr-10"
                    data-testid="password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#52525b] hover:text-white"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label className="text-white">手机号（选填）</Label>
                <Input
                  value={formData.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  placeholder="请输入手机号"
                  className="bg-[#0a0e17] border-[#2a2f3e] text-white"
                  data-testid="phone-input"
                />
              </div>
            </CardContent>
          </Card>
        )}
        
        {/* 步骤2: 生辰信息 */}
        {step === 2 && (
          <Card className="bg-[#141824] border-[#f0a500]/30">
            <CardHeader>
              <CardTitle className="text-[#f0a500] flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                生辰信息
              </CardTitle>
              <CardDescription className="text-[#a1a1aa]">
                填写您的出生信息，用于计算八字命盘
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-white">姓名 *</Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    placeholder="请输入姓名"
                    className="bg-[#0a0e17] border-[#2a2f3e] text-white"
                    data-testid="name-input"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label className="text-white">性别 *</Label>
                  <Select value={formData.gender} onValueChange={(v) => handleInputChange('gender', v)}>
                    <SelectTrigger className="bg-[#0a0e17] border-[#2a2f3e] text-white" data-testid="gender-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="男">男</SelectItem>
                      <SelectItem value="女">女</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label className="text-white">出生年</Label>
                  <Select 
                    value={String(formData.birth_year)} 
                    onValueChange={(v) => handleInputChange('birth_year', parseInt(v))}
                  >
                    <SelectTrigger className="bg-[#0a0e17] border-[#2a2f3e] text-white" data-testid="year-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="max-h-60">
                      {YEARS.map(year => (
                        <SelectItem key={year} value={String(year)}>{year}年</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label className="text-white">出生月</Label>
                  <Select 
                    value={String(formData.birth_month)} 
                    onValueChange={(v) => handleInputChange('birth_month', parseInt(v))}
                  >
                    <SelectTrigger className="bg-[#0a0e17] border-[#2a2f3e] text-white" data-testid="month-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {MONTHS.map(month => (
                        <SelectItem key={month} value={String(month)}>{month}月</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label className="text-white">出生日</Label>
                  <Select 
                    value={String(formData.birth_day)} 
                    onValueChange={(v) => handleInputChange('birth_day', parseInt(v))}
                  >
                    <SelectTrigger className="bg-[#0a0e17] border-[#2a2f3e] text-white" data-testid="day-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {DAYS.map(day => (
                        <SelectItem key={day} value={String(day)}>{day}日</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label className="text-white flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  出生时辰
                </Label>
                <Select 
                  value={formData.birth_hour} 
                  onValueChange={(v) => handleInputChange('birth_hour', v)}
                >
                  <SelectTrigger className="bg-[#0a0e17] border-[#2a2f3e] text-white" data-testid="hour-select">
                    <SelectValue placeholder="选择时辰" />
                  </SelectTrigger>
                  <SelectContent>
                    {shichenOptions.map(option => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-[#52525b]">若不知出生时间，选择"不知道"将仅排年月日三柱</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-white flex items-center gap-2">
                    <MapPin className="w-4 h-4" />
                    出生省份
                  </Label>
                  <Select 
                    value={formData.birth_province} 
                    onValueChange={(v) => handleInputChange('birth_province', v)}
                  >
                    <SelectTrigger className="bg-[#0a0e17] border-[#2a2f3e] text-white" data-testid="province-select">
                      <SelectValue placeholder="选择省份" />
                    </SelectTrigger>
                    <SelectContent className="max-h-60">
                      {provinces.map(prov => (
                        <SelectItem key={prov} value={prov}>{prov}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label className="text-white">出生城市</Label>
                  <Select 
                    value={formData.birth_city} 
                    onValueChange={(v) => handleInputChange('birth_city', v)}
                    disabled={!formData.birth_province}
                  >
                    <SelectTrigger className="bg-[#0a0e17] border-[#2a2f3e] text-white" data-testid="city-select">
                      <SelectValue placeholder="选择城市" />
                    </SelectTrigger>
                    <SelectContent className="max-h-60">
                      {cities.map(city => (
                        <SelectItem key={city} value={city}>{city}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <p className="text-xs text-[#52525b]">出生地用于校正当地真太阳时，提升命盘精准度</p>
            </CardContent>
          </Card>
        )}
        
        {/* 步骤3: 命盘生成预览 */}
        {step === 3 && (
          <Card className="bg-[#141824] border-[#f0a500]/30">
            <CardHeader>
              <CardTitle className="text-[#f0a500]">命盘预览</CardTitle>
              <CardDescription className="text-[#a1a1aa]">
                确认您的命盘信息
              </CardDescription>
            </CardHeader>
            <CardContent>
              {baziPreview ? (
                <div className="space-y-4">
                  {/* 四柱八字 */}
                  <div className="bg-[#0a0e17] rounded-sm p-4 border border-[#f0a500]/20">
                    <h3 className="text-[#f0a500] text-sm mb-3">四柱八字</h3>
                    <div className="grid grid-cols-4 gap-2 text-center">
                      {['hour', 'day', 'month', 'year'].map((pillar) => {
                        const data = baziPreview.sizhu[pillar];
                        if (!data) return (
                          <div key={pillar} className="space-y-1">
                            <div className="text-xs text-[#52525b]">时柱</div>
                            <div className="text-lg text-[#52525b]">—</div>
                            <div className="text-lg text-[#52525b]">—</div>
                          </div>
                        );
                        return (
                          <div key={pillar} className="space-y-1">
                            <div className="text-xs text-[#52525b]">{data.label}</div>
                            <div className="text-lg text-[#f0a500] font-bold">{data.gan}</div>
                            <div className="text-lg text-[#c0392b] font-bold">{data.zhi}</div>
                            {data.shengxiao && (
                              <div className="text-xs text-[#a1a1aa]">{data.shengxiao}</div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                  
                  {/* 五行统计 */}
                  <div className="bg-[#0a0e17] rounded-sm p-4 border border-[#f0a500]/20">
                    <h3 className="text-[#f0a500] text-sm mb-3">五行分布</h3>
                    <div className="flex justify-between">
                      {baziPreview.wuxing_chart.map(item => (
                        <div key={item.name} className="text-center">
                          <div className="text-2xl font-bold" style={{ color: item.color }}>
                            {item.value}
                          </div>
                          <div className="text-xs text-[#a1a1aa]">{item.name}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  {/* 喜忌神 */}
                  <div className="bg-[#0a0e17] rounded-sm p-4 border border-[#f0a500]/20">
                    <h3 className="text-[#f0a500] text-sm mb-3">喜忌神</h3>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-xs text-[#52525b]">喜神</div>
                        <div className="text-lg text-green-500 font-bold">{baziPreview.xiyong.xi_shen}</div>
                      </div>
                      <div>
                        <div className="text-xs text-[#52525b]">用神</div>
                        <div className="text-lg text-blue-500 font-bold">{baziPreview.xiyong.yong_shen}</div>
                      </div>
                      <div>
                        <div className="text-xs text-[#52525b]">忌神</div>
                        <div className="text-lg text-red-500 font-bold">{baziPreview.xiyong.ji_shen}</div>
                      </div>
                    </div>
                  </div>
                  
                  {/* 生肖运势 */}
                  <div className="bg-[#0a0e17] rounded-sm p-4 border border-[#f0a500]/20">
                    <h3 className="text-[#f0a500] text-sm mb-3">2026年运势</h3>
                    <div className="flex items-center justify-between">
                      <div className="text-white">
                        生肖: {baziPreview.liunian_2026.birth_shengxiao}
                      </div>
                      <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                        baziPreview.liunian_2026.zodiac_fortune.rating === '大吉' ? 'bg-green-500/20 text-green-500' :
                        baziPreview.liunian_2026.zodiac_fortune.rating === '吉' ? 'bg-blue-500/20 text-blue-500' :
                        baziPreview.liunian_2026.zodiac_fortune.rating === '凶' ? 'bg-red-500/20 text-red-500' :
                        'bg-yellow-500/20 text-yellow-500'
                      }`}>
                        {baziPreview.liunian_2026.zodiac_fortune.rating}
                      </div>
                    </div>
                    <p className="text-sm text-[#a1a1aa] mt-2">
                      {baziPreview.liunian_2026.zodiac_fortune.advice}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-8 h-8 animate-spin text-[#f0a500]" />
                </div>
              )}
            </CardContent>
          </Card>
        )}
        
        {/* 导航按钮 */}
        <div className="flex justify-between mt-6">
          <Button
            variant="outline"
            onClick={prevStep}
            disabled={step === 1}
            className="border-[#2a2f3e] text-white hover:bg-[#1e2330]"
            data-testid="prev-step-btn"
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            上一步
          </Button>
          
          {step < 3 ? (
            <Button
              onClick={nextStep}
              className="bg-[#f0a500] hover:bg-[#f0a500]/80 text-black"
              data-testid="next-step-btn"
            >
              下一步
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          ) : (
            <Button
              onClick={handleSubmit}
              disabled={loading}
              className="bg-[#f0a500] hover:bg-[#f0a500]/80 text-black"
              data-testid="submit-btn"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  注册中...
                </>
              ) : (
                '完成注册'
              )}
            </Button>
          )}
        </div>
        
        {/* 登录链接 */}
        <div className="text-center mt-6">
          <p className="text-[#52525b]">
            已有账户？
            <button
              onClick={() => navigate('/login')}
              className="text-[#f0a500] hover:underline ml-1"
            >
              立即登录
            </button>
          </p>
        </div>
        
        {/* 免责声明 */}
        <div className="mt-8 text-center">
          <p className="text-xs text-[#52525b]">
            ⚠️ 以上内容基于命理推算，仅供娱乐参考，不构成投资建议
          </p>
        </div>
      </div>
    </div>
  );
}
