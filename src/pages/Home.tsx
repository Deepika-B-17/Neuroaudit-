import { Brain, Fingerprint, Gauge, HeartPulse, ShieldCheck } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { EEGChart } from '../components/eeg/EEGChart'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'

const steps = [
  { n: '01', title: 'Upload EEG', body: 'Provide a recording in a common research format.' },
  { n: '02', title: 'Analyze Signal', body: 'Review structure used for a privacy-oriented assessment.' },
  { n: '03', title: 'Assess Privacy Risk', body: 'Estimate exposure across four inference dimensions.' },
  { n: '04', title: 'Get Recommendations', body: 'Apply practical controls for stored neural data.' },
  { n: '05', title: 'Generate Report', body: 'Export a structured audit summary for review.' },
]

const dimensions = [
  {
    icon: Fingerprint,
    title: 'Identity',
    body: 'Estimated exposure to identity-related inference from signal structure.',
  },
  {
    icon: HeartPulse,
    title: 'Emotion',
    body: 'Estimated exposure to emotion-related inference in model-dependent settings.',
  },
  {
    icon: ShieldCheck,
    title: 'Stress',
    body: 'Estimated exposure to stress-related inference without clinical claims.',
  },
  {
    icon: Gauge,
    title: 'Mental Workload',
    body: 'Estimated exposure to cognitive-workload inference under task-sensitive models.',
  },
]

export function Home() {
  const navigate = useNavigate()

  return (
    <div>
      <section className="mx-auto grid max-w-6xl items-center gap-12 px-5 py-16 lg:grid-cols-[1.05fr_0.95fr] lg:py-20">
        <div>
          <p className="text-[11px] font-semibold tracking-[0.22em] text-accent">NEURAL DATA PRIVACY</p>
          <h1 className="mt-4 max-w-xl text-4xl font-bold tracking-tight text-foreground md:text-[2.75rem] md:leading-[1.15]">
            What Can Your EEG Data Reveal?
          </h1>
          <p className="mt-5 max-w-lg text-base leading-relaxed text-muted">
            Assess potential privacy exposure in neural data before it becomes a security risk.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Button onClick={() => navigate('/audit/new')}>Start New Audit →</Button>
            <Button variant="secondary" onClick={() => document.getElementById('how-it-works')?.scrollIntoView()}>
              Explore How It Works
            </Button>
          </div>
        </div>
        <Card elevated className="overflow-hidden p-4 md:p-5">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold tracking-[0.14em] uppercase text-muted">EEG Signal</p>
              <p className="text-sm font-medium">10-channel preview · demonstration</p>
            </div>
            <div className="flex gap-3 text-[11px] text-muted">
              <span>Fs 256 Hz</span>
              <span>10 ch</span>
            </div>
          </div>
          <EEGChart animated height={280} />
        </Card>
      </section>

      <section className="border-y border-border bg-section">
        <div className="mx-auto grid max-w-6xl gap-10 px-5 py-14 md:grid-cols-3">
          {[
            { icon: Brain, title: 'Understand', body: 'Identify what neural data may reveal.' },
            { icon: Gauge, title: 'Assess', body: 'Measure potential privacy exposure.' },
            { icon: ShieldCheck, title: 'Protect', body: 'Apply security recommendations.' },
          ].map((item) => (
            <div key={item.title} className="flex gap-4">
              <item.icon className="mt-0.5 h-5 w-5 text-accent" aria-hidden />
              <div>
                <h2 className="text-sm font-semibold tracking-[0.16em] uppercase">{item.title}</h2>
                <p className="mt-2 text-sm leading-relaxed text-muted">{item.body}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section id="how-it-works" className="mx-auto max-w-6xl px-5 py-16">
        <p className="text-[11px] font-semibold tracking-[0.18em] uppercase text-muted">Workflow</p>
        <h2 className="mt-2 text-2xl font-bold tracking-tight">How it works</h2>
        <div className="mt-10 hidden md:grid md:grid-cols-5 md:gap-4">
          {steps.map((step, i) => (
            <div key={step.n} className="relative">
              {i < steps.length - 1 && (
                <div className="absolute left-[28%] top-3 h-px w-[72%] bg-border" aria-hidden />
              )}
              <p className="text-xs font-semibold text-accent">{step.n}</p>
              <h3 className="mt-3 text-sm font-semibold">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{step.body}</p>
            </div>
          ))}
        </div>
        <ol className="mt-8 space-y-6 md:hidden">
          {steps.map((step) => (
            <li key={step.n}>
              <p className="text-xs font-semibold text-accent">{step.n}</p>
              <h3 className="mt-1 font-semibold">{step.title}</h3>
              <p className="mt-1 text-sm text-muted">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="mx-auto max-w-6xl px-5 pb-16">
        <p className="text-[11px] font-semibold tracking-[0.18em] uppercase text-muted">Dimensions</p>
        <h2 className="mt-2 text-2xl font-bold tracking-tight">What we assess</h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {dimensions.map((d) => (
            <Card key={d.title} className="p-5">
              <d.icon className="h-4 w-4 text-accent" aria-hidden />
              <h3 className="mt-3 font-semibold">{d.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{d.body}</p>
              <div className="mt-4 opacity-80">
                <EEGChart channels={['C3', 'C4']} height={56} compact showTimeAxis={false} />
              </div>
            </Card>
          ))}
        </div>
      </section>

      <section className="border-t border-border bg-section">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-6 px-5 py-14 md:flex-row md:items-center">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Your neural data deserves privacy.</h2>
            <p className="mt-2 text-sm text-muted">Start with a structured privacy risk assessment of an EEG recording.</p>
          </div>
          <Button onClick={() => navigate('/audit/new')}>Start New Audit →</Button>
        </div>
      </section>
    </div>
  )
}
