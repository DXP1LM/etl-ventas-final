import { Component, OnInit, ViewChild, AfterViewInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { SalesService, Venta } from '../../services/sales.service';

@Component({
  selector: 'app-tabla',
  standalone: true,
  imports: [
    CommonModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatFormFieldModule,
    MatInputModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatChipsModule,
    MatProgressBarModule
  ],
  templateUrl: './tabla.component.html',
  styleUrls: ['./tabla.component.css']
})
export class TablaComponent implements OnInit, AfterViewInit {
  private readonly salesService = inject(SalesService);

  displayedColumns: string[] = [
    'id_transaccion',
    'categoria',
    'producto',
    'cantidad',
    'precio_unitario',
    'fecha_venta',
    'stock_actual',
    'monto_total',
    'igv'
  ];

  dataSource = new MatTableDataSource<Venta>([]);
  totalRegistros = signal<number>(0);
  loading = signal<boolean>(true);
  filtroActual = signal<string>('');

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  ngOnInit(): void {
    this.cargarVentas();
  }

  ngAfterViewInit(): void {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
  }

  cargarVentas(): void {
    this.loading.set(true);
    this.salesService.getVentas().subscribe({
      next: (resp) => {
        this.dataSource.data = resp.data;
        this.totalRegistros.set(resp.total);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Error al cargar ventas:', err);
        this.loading.set(false);
      }
    });
  }

  aplicarFiltro(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value;
    this.filtroActual.set(filterValue);
    this.dataSource.filter = filterValue.trim().toLowerCase();

    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
  }

  filtrarPorCategoria(categoria: string): void {
    if (this.filtroActual() === categoria) {
      this.limpiarFiltro();
      return;
    }
    this.filtroActual.set(categoria);
    this.dataSource.filter = categoria.trim().toLowerCase();
    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
  }

  limpiarFiltro(): void {
    this.filtroActual.set('');
    this.dataSource.filter = '';
  }

  obtenerClaseCategoria(categoria: string): string {
    const mapa: Record<string, string> = {
      'Tecnología': 'chip-tech',
      'Electro': 'chip-electro',
      'Calzado': 'chip-calzado',
      'Hogar': 'chip-hogar',
      'Ropa': 'chip-ropa'
    };
    return mapa[categoria] || 'chip-default';
  }
}

