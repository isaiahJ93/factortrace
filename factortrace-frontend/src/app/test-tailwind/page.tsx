export default function TestPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-5xl font-bold text-white mb-8 text-center">
          Tailwind CSS Test
        </h1>
        
        <div className="bg-white rounded-lg shadow-2xl p-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            If you can see this styled card...
          </h2>
          <p className="text-gray-600 mb-4">
            ✅ Tailwind CSS is working correctly!
          </p>
          
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-red-500 text-white p-4 rounded text-center">Red</div>
            <div className="bg-green-500 text-white p-4 rounded text-center">Green</div>
            <div className="bg-blue-500 text-white p-4 rounded text-center">Blue</div>
          </div>
          
          <button className="mt-6 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-3 rounded-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition-all transform hover:scale-105">
            Click Me!
          </button>
        </div>
      </div>
    </div>
  )
}