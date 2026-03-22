import { useState } from 'react'
import './App.css'
import CICDDashboard from './components/CICDDashboard'
import PipelineButton from './components/PipelineButton'

function App() {

  return (
    <>
      <h1>Hello</h1>
      <CICDDashboard />
      <PipelineButton />
    </>
  )

}

export default App