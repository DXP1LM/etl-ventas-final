import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Venta {
  id_transaccion: string;
  categoria: string;
  producto: string;
  cantidad: number;
  precio_unitario: number;
  fecha_venta: string;
  stock_actual: number;
  monto_total: number;
  igv: number;
}

export interface VentasResponse {
  total: number;
  data: Venta[];
}

export interface KpiResponse {
  total_transacciones: number;
  total_unidades: number;
  total_ingresos: number;
  total_igv: number;
  total_categorias: number;
}

export interface TotalesCategoriaResponse {
  categorias: string[];
  monto_total: number[];
  igv: number[];
  detalles: {
    categoria: string;
    monto_total: number;
    igv: number;
  }[];
}

export interface UnidadesCategoriaResponse {
  categorias: string[];
  unidades: number[];
  porcentajes: number[];
  total_unidades: number;
}

@Injectable({
  providedIn: 'root'
})
export class SalesService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = 'http://localhost:5000/api';

  getVentas(): Observable<VentasResponse> {
    return this.http.get<VentasResponse>(`${this.apiUrl}/ventas`);
  }

  getKpis(): Observable<KpiResponse> {
    return this.http.get<KpiResponse>(`${this.apiUrl}/dashboard/kpis`);
  }

  getTotalesPorCategoria(): Observable<TotalesCategoriaResponse> {
    return this.http.get<TotalesCategoriaResponse>(`${this.apiUrl}/dashboard/totales-por-categoria`);
  }

  getUnidadesPorCategoria(): Observable<UnidadesCategoriaResponse> {
    return this.http.get<UnidadesCategoriaResponse>(`${this.apiUrl}/dashboard/unidades-por-categoria`);
  }

  getHealth(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/health`);
  }
}

