import './App.css';
import Header from './Header';
import Comparison from './Comparison';

function App() {
  return (
    <div className='flex justify-center bg-gray-800'>
      <div className='max-w-[1200px]'>
        <Header />
        <Comparison />
      </div>
    </div>
  );
}

export default App;
