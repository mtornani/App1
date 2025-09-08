'use client'

import { useState, useEffect } from 'react'
import PlayerCard from '@/components/PlayerCard'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function Home() {
  const [players, setPlayers] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchPlayers()
  }, [])

  const fetchPlayers = async () => {
    try {
      setLoading(true)
      const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/players`)
      const data = await res.json()
      setPlayers(data)
    } catch (error) {
      console.error('Error fetching players:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    try {
      setLoading(true)
      await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/run/refresh`, {
        method: 'POST'
      })
      fetchPlayers()
    } catch (error) {
      console.error('Error refreshing ', error)
    }
  }

  const handleExport = async (format: string) => {
    try {
      window.open(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/export?format=${format}`, '_blank')
    } catch (error) {
      console.error('Error exporting data:', error)
    }
  }

  const filteredPlayers = players.filter(player => 
    player.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    player.club.toLowerCase().includes(searchTerm.toLowerCase()) ||
    player.nationality.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="container mx-auto py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Radar SMR - Calciatori Eleggibili</h1>
        <div className="flex gap-2">
          <Button onClick={() => handleRefresh()} disabled={loading}>
            {loading ? 'Aggiornamento...' : 'Aggiorna Dati'}
          </Button>
          <Button onClick={() => handleExport('csv')} variant="outline">
            Esporta CSV
          </Button>
          <Button onClick={() => handleExport('json')} variant="outline">
            Esporta JSON
          </Button>
        </div>
      </div>

      <div className="mb-6">
        <Input
          placeholder="Cerca per nome, club o nazionalità..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-md"
        />
      </div>

      {loading && players.length === 0 ? (
        <div className="text-center py-12">
          <p>Caricamento dati...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPlayers.map((player: any) => (
            <PlayerCard key={player.id} player={player} />
          ))}
        </div>
      )}

      {filteredPlayers.length === 0 && !loading && (
        <div className="text-center py-12">
          <p>Nessun calciatore trovato.</p>
        </div>
      )}
    </div>
  )
}
