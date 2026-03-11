/**
 * 用户登录页面
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Lock, Eye, EyeOff, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { authService, userStorage } from '../services/authService';

export default function LoginPage() {
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  
  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.username || !formData.password) {
      toast.error('请填写用户名和密码');
      return;
    }
    
    setLoading(true);
    try {
      const res = await authService.login(formData);
      if (res.success) {
        userStorage.setUser(res.user);
        toast.success('登录成功！');
        navigate('/profile');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || '登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center py-8 px-4">
      {/* 八卦纹路背景 */}
      <div className="fixed inset-0 opacity-5 pointer-events-none">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23f0a500' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }} />
      </div>
      
      <Card className="w-full max-w-md bg-[#141824] border-[#f0a500]/30 relative z-10">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 rounded-full bg-[#f0a500]/10 flex items-center justify-center mb-4">
            <User className="w-8 h-8 text-[#f0a500]" />
          </div>
          <CardTitle className="text-2xl text-[#f0a500]">用户登录</CardTitle>
          <CardDescription className="text-[#a1a1aa]">
            登录查看您的命盘和投资建议
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label className="text-white">用户名</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#52525b]" />
                <Input
                  value={formData.username}
                  onChange={(e) => handleInputChange('username', e.target.value)}
                  placeholder="请输入用户名"
                  className="bg-[#0a0e17] border-[#2a2f3e] text-white pl-10"
                  data-testid="login-username"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label className="text-white">密码</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#52525b]" />
                <Input
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  placeholder="请输入密码"
                  className="bg-[#0a0e17] border-[#2a2f3e] text-white pl-10 pr-10"
                  data-testid="login-password"
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
            
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-[#f0a500] hover:bg-[#f0a500]/80 text-black"
              data-testid="login-submit"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  登录中...
                </>
              ) : (
                '登录'
              )}
            </Button>
          </form>
          
          <div className="mt-6 text-center">
            <p className="text-[#52525b]">
              还没有账户？
              <button
                onClick={() => navigate('/register')}
                className="text-[#f0a500] hover:underline ml-1"
              >
                立即注册
              </button>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
