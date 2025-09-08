'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import PlayerDetail from '@/components/PlayerDetail'
import { Button } from '@/components/ui/button'

export default function PlayerPage() {
  const params = useParams()
  const [player, setPlayer] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (params.id) {
      fetchPlayer()
    }
  }, [params.id])

  const fetchPlayer = async () => {
    try {
      setLoading(true)
      const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/players/${params.id}`)
      const data = await res.json()
      setPlayer(data)
    } catch (error) {
      console.error('Error fetching player:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center py-12">
          <p>Caricamento dettagli giocatore...</p>
        </div>
      </div>
    )
  }

  if (!player) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center py-12">
          <p>Giocatore non trovato.</p>
          <Button onClick={() => window.history.back()} className="mt-4">
            Torna indietro
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8">
      <PlayerDetail player={player} />
    </div>
  )
}
