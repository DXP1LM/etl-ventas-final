import { Component, OnInit, AfterViewInit, ViewChild, ElementRef, OnDestroy, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Chart, registerables } from 'chart.js';
import { SalesService, KpiResponse } from '../../services/sales.service';

Chart.register(...registerables);

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit, AfterViewInit, OnDestroy {
  private readonly salesService = inject(SalesService);

  @ViewChild('barCanvas') barCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('donutCanvas') donutCanvas!: ElementRef<HTMLCanvasElement>;

  private barChartInstance?: Chart;
  private donutChartInstance?: Chart;

  kpis = signal<KpiResponse | null>(null);
  loading = signal<boolean>(true);
  errorMsg = signal<string | null>(null);

  private viewInitialized = false;
  private pendingBarData: any = null;
  private pendingDonutData: any = null;

  ngOnInit(): void {
    this.cargarDatos();
  }

  ngAfterViewInit(): void {
    this.viewInitialized = true;
    if (this.pendingBarData) {
      this.renderBarChart(this.pendingBarData);
    }
    if (this.pendingDonutData) {
      this.renderDonutChart(this.pendingDonutData);
    }
  }

  ngOnDestroy(): void {
    if (this.barChartInstance) {
      this.barChartInstance.destroy();
    }
    if (this.donutChartInstance) {
      this.donutChartInstance.destroy();
    }
  }

  cargarDatos(): void {
    this.loading.set(true);
    this.errorMsg.set(null);

    // Cargar KPIs
    this.salesService.getKpis().subscribe({
      next: (kpis) => this.kpis.set(kpis),
      error: (err) => {
        console.error('Error cargando KPIs:', err);
        this.errorMsg.set('No se pudo conectar con el microservicio Backend (http://localhost:5000). Asegúrate de que app.py esté corriendo.');
      }
    });

    // Cargar Gráfico 1: Barras Verticales (monto_total vs igv)
    this.salesService.getTotalesPorCategoria().subscribe({
      next: (res) => {
        this.pendingBarData = res;
        if (this.viewInitialized && this.barCanvas) {
          this.renderBarChart(res);
        }
      },
      error: (err) => console.error('Error cargando totales por categoría:', err)
    });

    // Cargar Gráfico 2: Torta / Dona (unidades por categoría)
    this.salesService.getUnidadesPorCategoria().subscribe({
      next: (res) => {
        this.pendingDonutData = res;
        if (this.viewInitialized && this.donutCanvas) {
          this.renderDonutChart(res);
        }
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Error cargando unidades por categoría:', err);
        this.loading.set(false);
      }
    });
  }

  private renderBarChart(data: any): void {
    if (!this.barCanvas) return;
    if (this.barChartInstance) {
      this.barChartInstance.destroy();
    }

    const ctx = this.barCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    this.barChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.categorias,
        datasets: [
          {
            label: 'Monto Total (S/)',
            data: data.monto_total,
            backgroundColor: 'rgba(54, 88, 226, 0.85)',
            borderColor: 'rgba(54, 88, 226, 1)',
            borderWidth: 1.5,
            borderRadius: 6
          },
          {
            label: 'IGV 18% (S/)',
            data: data.igv,
            backgroundColor: 'rgba(255, 159, 28, 0.85)',
            borderColor: 'rgba(255, 159, 28, 1)',
            borderWidth: 1.5,
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              boxWidth: 14,
              font: { size: 12, family: 'Roboto' }
            }
          },
          tooltip: {
            callbacks: {
              label: (item) => ` ${item.dataset.label}: S/ ${Number(item.raw).toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (val) => `S/ ${Number(val).toLocaleString('es-PE')}`
            },
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        }
      }
    });
  }

  private renderDonutChart(data: any): void {
    if (!this.donutCanvas) return;
    if (this.donutChartInstance) {
      this.donutChartInstance.destroy();
    }

    const ctx = this.donutCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    const backgroundColors = [
      '#2563eb', // Azul
      '#06b6d4', // Cyan
      '#10b981', // Verde esmeralda
      '#f59e0b', // Ámbar
      '#ef4444'  // Rojo carmesí
    ];

    this.donutChartInstance = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: data.categorias,
        datasets: [
          {
            data: data.unidades,
            backgroundColor: backgroundColors,
            borderColor: '#ffffff',
            borderWidth: 3,
            hoverOffset: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '62%',
        plugins: {
          legend: {
            position: 'right',
            labels: {
              boxWidth: 14,
              font: { size: 12, family: 'Roboto' }
            }
          },
          tooltip: {
            callbacks: {
              label: (item) => {
                const total = data.total_unidades;
                const value = Number(item.raw);
                const pct = ((value / total) * 100).toFixed(1);
                return ` ${item.label}: ${value.toLocaleString()} unidades (${pct}%)`;
              }
            }
          }
        }
      }
    });
  }
}

