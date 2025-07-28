export default function StyleTest() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Tailwind CSS Test
        </h1>
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <h2 className="text-xl font-semibold text-blue-600">Card 1</h2>
            <p className="text-gray-600 mt-2">If you see styled cards, Tailwind is working!</p>
          </div>
          <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-6 rounded-lg shadow-lg text-white">
            <h2 className="text-xl font-semibold">Card 2</h2>
            <p className="mt-2">Gradient background test</p>
          </div>
          <div className="bg-emerald-500 p-6 rounded-lg shadow-lg text-white">
            <h2 className="text-xl font-semibold">Card 3</h2>
            <p className="mt-2">Solid color test</p>
          </div>
        </div>
      </div>
    </div>
  )
}