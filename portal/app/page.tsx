import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center space-y-8">
        <h1 className="text-6xl font-bold text-gray-900">
          Opti<span className="text-primary-600">Infra</span>
        </h1>
        
        <p className="text-xl text-gray-600 max-w-2xl">
          AI-Powered LLM Infrastructure Optimization
        </p>
        
        <div className="flex gap-4 justify-center">
          <Link
            href="/dashboard"
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Go to Dashboard
          </Link>
          
          <Link
            href="/api/health"
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            API Health
          </Link>
        </div>
        
        <div className="grid grid-cols-3 gap-8 mt-16 max-w-3xl">
          <div className="text-center">
            <div className="text-4xl font-bold text-primary-600">50%</div>
            <div className="text-sm text-gray-600 mt-2">Cost Reduction</div>
          </div>
          
          <div className="text-center">
            <div className="text-4xl font-bold text-primary-600">3x</div>
            <div className="text-sm text-gray-600 mt-2">Performance Boost</div>
          </div>
          
          <div className="text-center">
            <div className="text-4xl font-bold text-primary-600">4</div>
            <div className="text-sm text-gray-600 mt-2">AI Agents</div>
          </div>
        </div>
      </div>
    </main>
  );
}
