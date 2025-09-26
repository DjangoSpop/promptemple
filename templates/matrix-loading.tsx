import { useState, useEffect, useRef } from 'react';

interface EgyptianLoadingProps {
  isLoading: boolean;
  message?: string;
}

const EgyptianLoading: React.FC<EgyptianLoadingProps> = ({ 
  isLoading, 
  message = "Deciphering ancient wisdom..." 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [dots, setDots] = useState('');

  // Egyptian hieroglyphic rain effect
  useEffect(() => {
    if (!isLoading || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = 500;
    canvas.height = 250;

    // Egyptian hieroglyphic symbols (Unicode)
    const hieroglyphs = [
      '𓀀', '𓀁', '𓀂', '𓀃', '𓀄', '𓀅', '𓀆', '𓀇', '𓀈', '𓀉', '𓀊', '𓀋', '𓀌', '𓀍', '𓀎', '𓀏',
      '𓀐', '𓀑', '𓀒', '𓀓', '𓀔', '𓀕', '𓀖', '𓀗', '𓀘', '𓀙', '𓀚', '𓀛', '𓀜', '𓀝', '𓀞', '𓀟',
      '𓁀', '𓁁', '𓁂', '𓁃', '𓁄', '𓁅', '𓁆', '𓁇', '𓁈', '𓁉', '𓁊', '𓁋', '𓁌', '𓁍', '𓁎', '𓁏',
      '𓂀', '𓂁', '𓂂', '𓂃', '𓂄', '𓂅', '𓂆', '𓂇', '𓂈', '𓂉', '𓂊', '𓂋', '𓂌', '𓂍', '𓂎', '𓂏',
      '𓃀', '𓃁', '𓃂', '𓃃', '𓃄', '𓃅', '𓃆', '𓃇', '𓃈', '𓃉', '𓃊', '𓃋', '𓃌', '𓃍', '𓃎', '𓃏'
    ];

    const fontSize = 16;
    const columns = Math.floor(canvas.width / fontSize);

    const drops: number[] = [];
    for (let x = 0; x < columns; x++) {
      drops[x] = Math.random() * -100; // Start at different times
    }

    const draw = () => {
      // Dark sand/papyrus background with slight transparency for trail effect
      ctx.fillStyle = 'rgba(20, 16, 10, 0.05)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Golden/yellow hieroglyphic text with gradient effect
      const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
      gradient.addColorStop(0, '#FFD700'); // Gold
      gradient.addColorStop(0.5, '#FFA500'); // Orange
      gradient.addColorStop(1, '#DAA520'); // Goldenrod
      
      ctx.fillStyle = gradient;
      ctx.font = `${fontSize}px "Noto Sans Egyptian Hieroglyphs", serif`;
      ctx.shadowColor = '#FFD700';
      ctx.shadowBlur = 3;

      for (let i = 0; i < drops.length; i++) {
        const symbol = hieroglyphs[Math.floor(Math.random() * hieroglyphs.length)];
        const x = i * fontSize;
        const y = drops[i] * fontSize;
        
        // Add some glow effect
        ctx.shadowBlur = Math.random() * 5 + 2;
        ctx.fillText(symbol, x, y);

        // Reset to top with some randomness
        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
          drops[i] = 0;
        }
        drops[i]++;
      }
      
      ctx.shadowBlur = 0; // Reset shadow
    };

    const interval = setInterval(draw, 80); // Slower, more mystical pace

    return () => clearInterval(interval);
  }, [isLoading]);

  // Animated dots for thinking message
  useEffect(() => {
    if (!isLoading) {
      setDots('');
      return;
    }

    const interval = setInterval(() => {
      setDots(prev => {
        if (prev.length >= 3) return '';
        return prev + '.';
      });
    }, 600);

    return () => clearInterval(interval);
  }, [isLoading]);

  if (!isLoading) return null;

  return (
    <div className="fixed inset-0 bg-gradient-to-b from-amber-950 via-yellow-900 to-orange-950 bg-opacity-95 flex items-center justify-center z-50">
      <div className="text-center">
        {/* Hieroglyphic Canvas */}
        <div className="relative mb-8">
          <canvas
            ref={canvasRef}
            className="border-2 border-yellow-600 rounded-lg shadow-2xl shadow-yellow-600/30"
            style={{ 
              background: 'linear-gradient(135deg, #2D1810 0%, #1A1008 50%, #0F0A05 100%)',
              boxShadow: 'inset 0 0 20px rgba(255, 215, 0, 0.1)'
            }}
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="bg-gradient-to-r from-amber-900/90 to-yellow-900/90 px-6 py-3 rounded-lg border border-yellow-600 backdrop-blur-sm">
              <span className="text-yellow-300 font-serif text-sm tracking-wide">
                ⚱️ ANCIENT KNOWLEDGE SYSTEM ACTIVE ⚱️
              </span>
            </div>
          </div>
        </div>

        {/* Egyptian styled thinking message */}
        <div className="text-yellow-300 font-serif text-xl mb-6 tracking-wide">
          <span className="inline-block animate-pulse">𓋹</span>
          {' '}{message}{dots}{' '}
          <span className="inline-block animate-pulse">𓋹</span>
        </div>

        {/* Papyrus-style status bar */}
        <div className="w-96 bg-amber-900 rounded-full h-3 mb-6 border border-yellow-700 shadow-inner">
          <div className="bg-gradient-to-r from-yellow-500 via-yellow-400 to-amber-400 h-3 rounded-full animate-pulse shadow-lg shadow-yellow-500/50"
               style={{ width: '100%' }}></div>
        </div>

        {/* Egyptian themed loading text */}
        <div className="text-yellow-400 font-serif text-sm opacity-80 max-w-lg mx-auto">
          <div className="flex items-center justify-center space-x-4 mb-2">
            <span>𓂀 Consulting the scrolls</span>
            <span>𓃭 Awakening the scribes</span>
            <span>𓊪 Gathering wisdom</span>
          </div>
          <div className="text-xs text-yellow-500 mt-2">
            "In the halls of ancient knowledge, every query becomes sacred wisdom"
          </div>
        </div>

        {/* Animated Egyptian symbols */}
        <div className="mt-6 flex justify-center space-x-8 text-yellow-500 text-2xl">
          <span className="animate-bounce" style={{ animationDelay: '0s' }}>𓋹</span>
          <span className="animate-bounce" style={{ animationDelay: '0.2s' }}>𓊪</span>
          <span className="animate-bounce" style={{ animationDelay: '0.4s' }}>𓃭</span>
          <span className="animate-bounce" style={{ animationDelay: '0.6s' }}>𓂀</span>
          <span className="animate-bounce" style={{ animationDelay: '0.8s' }}>𓋹</span>
        </div>
      </div>
    </div>
  );
};

// Demo component to show the Egyptian loading in action
const EgyptianLoadingDemo = () => {
  const [isLoading, setIsLoading] = useState(false);

  const handleStartLoading = () => {
    setIsLoading(true);
    // Simulate loading time
    setTimeout(() => setIsLoading(false), 7000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-100 via-yellow-50 to-orange-100 p-8">
      <div className="max-w-3xl mx-auto text-center">
        <h1 className="text-4xl font-bold text-amber-900 mb-4 font-serif">
          𓋹 Egyptian Hieroglyphic Loading System 𓋹
        </h1>
        
        <p className="text-amber-700 mb-8 font-serif text-lg">
          "Where ancient wisdom meets modern AI"
        </p>
        
        <button
          onClick={handleStartLoading}
          disabled={isLoading}
          className="bg-gradient-to-r from-yellow-600 to-amber-600 hover:from-yellow-500 hover:to-amber-500 disabled:from-gray-500 disabled:to-gray-600 text-white px-8 py-4 rounded-lg font-serif transition-all duration-300 shadow-lg transform hover:scale-105"
        >
          {isLoading ? '𓊪 Consulting the Ancients...' : '𓂀 Awaken the Sacred Knowledge'}
        </button>

        <div className="mt-12 text-amber-800 text-left bg-yellow-50 p-6 rounded-lg border-2 border-yellow-200 shadow-lg">
          <h2 className="text-2xl font-bold mb-6 text-amber-900 font-serif">✨ Egyptian Theme Features:</h2>
          <div className="grid md:grid-cols-2 gap-4 font-serif">
            <div>
              <h3 className="font-bold text-amber-800 mb-2">Visual Elements:</h3>
              <ul className="space-y-2 text-sm">
                <li>• 𓋹 Authentic Egyptian hieroglyphic rain</li>
                <li>• 𓊪 Golden/amber color palette</li>
                <li>• 𓃭 Papyrus-style backgrounds</li>
                <li>• 𓂀 Mystical glow effects</li>
                <li>• ⚱️ Sacred symbol animations</li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold text-amber-800 mb-2">Cultural Integration:</h3>
              <ul className="space-y-2 text-sm">
                <li>• Unicode hieroglyphic characters</li>
                <li>• Ancient wisdom messaging</li>
                <li>• Egyptian-themed status text</li>
                <li>• Serif fonts for authenticity</li>
                <li>• Desert sand color gradients</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <EgyptianLoading 
        isLoading={isLoading} 
        message="Channeling the wisdom of the pharaohs" 
      />
    </div>
  );
};

export default EgyptianLoadingDemo;