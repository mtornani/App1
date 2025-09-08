'use client'

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import Link from "next/link"

interface PlayerCardProps {
  player: any
}

export default function PlayerCard({ player }: PlayerCardProps) {
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
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-xl">{player.name}</CardTitle>
            <CardDescription>{player.club}</CardDescription>
          </div>
          <Badge variant={getTrackColor(player.track)}>
            {player.track}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Nazionalità:</span>
            <span className="text-sm font-medium">{player.nationality}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Ruolo:</span>
            <span className="text-sm font-medium">{player.role || 'N/D'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Data di nascita:</span>
            <span className="text-sm font-medium">
              {player.dob ? new Date(player.dob).toLocaleDateString('it-IT') : 'N/D'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Cittadinanza:</span>
            <span className="text-sm font-medium">
              {getCitizenshipStatus(player.citizenship_status)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Score:</span>
            <span className="text-sm font-medium">{player.score || 'N/D'}</span>
          </div>
        </div>
        
        <div className="mt-4 flex gap-2">
          <Button variant="outline" size="sm" asChild>
            <Link href={`/player/${player.id}`}>Dettagli</Link>
          </Button>
          {player.sources && player.sources.length > 0 && (
            <Button variant="outline" size="sm" asChild>
              <a href={player.sources[0]} target="_blank" rel="noopener noreferrer">
                Fonte
              </a>
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
