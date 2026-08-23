import { useNavigate } from 'react-router-dom'
import { RecommendationCard } from '../components/recommendations/RecommendationCard'
import { Button } from '../components/ui/Button'
import { useAudit } from '../context/AuditSessionContext'

export function Recommendations() {
  const navigate = useNavigate()
  const { recommendations } = useAudit()

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="text-2xl font-bold tracking-tight">Security Recommendations</h1>
      <p className="mt-1 text-sm text-muted">Practical measures to reduce neural-data privacy exposure.</p>
      <div className="mt-8 grid gap-4">
        {recommendations.map((item) => (
          <RecommendationCard key={item.id} item={item} />
        ))}
      </div>
      <div className="mt-8">
        <Button onClick={() => navigate('/app/report')}>View Report →</Button>
      </div>
    </div>
  )
}
