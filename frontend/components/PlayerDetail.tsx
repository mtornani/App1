'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import Link from "next/link"

interface PlayerDetailProps {
  player: any
}

export default function PlayerDetail({ player }: PlayerDetailProps) {
  const getTrackColor = (track: string) => {
    switch (track) {
      case "NOW": return "success"
      case "WHAT_IF": return "warning"
      default: return "default"
    }
  }

  const getCitizenshipStatus = (status: string) => {
    switch (status) {
      case "has_SMR": return "Cittadino SMR"
      case "no_SMR": return "Non cittadino SMR"
      case "unknown": return "Stato sconosciuto"
      default: return status
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-2xl">{player.name}</CardTitle>
              <p className="text-lg text-muted-foreground">{player.club}</p>
            </div>
            <Badge variant={getTrackColor(player.track)} className="text-lg">
              {player.track}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="font-semibold mb-2">Informazioni Personali</h3>
              <div className="space-y-1 text-sm">
                <p><span className="text-muted-foreground">Data di nascita:</span> {player.dob ? new Date(player.dob).toLocaleDateString('it-IT') : 'N/D'}</p>
                <p><span className="text-muted-foreground">Nazionalità:</span> {player.nationality || 'N/D'}</p>
                <p><span className="text-muted-foreground">Ruolo:</span> {player.role || 'N/D'}</p>
              </div>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Valutazione Legale</h3>
              <div className="space-y-1 text-sm">
                <p><span className="text-muted-foreground">Cittadinanza SMR:</span> {getCitizenshipStatus(player.citizenship_status)}</p>
                <p><span className="text-muted-foreground">Tempo stimato:</span> {player.time_to_eligible_estimate !== undefined ? `${player.time_to_eligible_estimate} anni` : 'N/D'}</p>
                <p><span className="text-muted-foreground">Score:</span> {player.score || 'N/D'}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Dettaglio Legale</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-medium mb-2">Percorso di Naturalizzazione</h4>
              <p className="text-sm">{player.nat_path_feasibility || 'N/D'}</p>
            </div>
            
            {player.legal_notes && player.legal_notes.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Note Legali</h4>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  {player.legal_notes.map((note: string, index: number) => (
                    <li key={index}>{note}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {player.sources && player.sources.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Fonti</h4>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  {player.sources.map((source: string, index: number) => (
                    <li key={index}>
                      <a href={source} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                        Fonte {index + 1}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <Button asChild>
          <Link href="/">← Torna alla lista</Link>
        </Button>
        {player.sources && player.sources.length > 0 && (
          <Button variant="outline" asChild>
            <a href={player.sources[0]} target="_blank" rel="noopener noreferrer">
              Visita Fonte Originale
            </a>
          </Button>
        )}
      </div>
    </div>
  )
                                                        }
