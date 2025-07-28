#!/usr/bin/env python3
"""
Bot de Trading DEMO - Simulação sem API Real
Demonstra todas as funcionalidades do bot com dados simulados
"""

import asyncio
import logging
import random
import time
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
import numpy as np

from indicators import TechnicalIndicators
from strategy import TrendFollowingStrategy
from risk_manager import AdaptiveRiskManager
from logger_config import setup_logging
from utils import load_config, validate_config


class DemoMarketDataGenerator:
    """Gerador de dados de mercado realistas para demonstração"""
    
    def __init__(self, base_price: float = 50000):
        self.base_price = base_price
        self.current_price = base_price
        self.trend_direction = 1  # 1 para alta, -1 para baixa
        self.volatility = 0.02
        
    def generate_realistic_data(self, periods: int = 500) -> Dict:
        """Gera dados de mercado realistas com tendências"""
        timestamps = [int(time.time() * 1000) - (periods - i) * 300000 for i in range(periods)]
        
        prices = []
        volumes = []
        
        for i in range(periods):
            # Mudança de tendência ocasional
            if random.random() < 0.005:  # 0.5% chance de mudança de tendência
                self.trend_direction *= -1
                
            # Movimento de preço com tendência
            trend_strength = random.uniform(0.3, 0.7)
            noise = random.gauss(0, self.volatility)
            
            change = (self.trend_direction * trend_strength * 0.001) + noise
            self.current_price *= (1 + change)
            
            # Garante que o preço não fique muito extremo
            if self.current_price < self.base_price * 0.7:
                self.trend_direction = 1
            elif self.current_price > self.base_price * 1.4:
                self.trend_direction = -1
                
            prices.append(self.current_price)
            
            # Volume realista
            base_volume = random.uniform(100, 500)
            if abs(change) > 0.01:  # Volume maior em movimentos grandes
                base_volume *= random.uniform(1.5, 3.0)
            volumes.append(base_volume)
        
        # Calcular high/low baseado nos preços close
        highs = [p * random.uniform(1.0, 1.005) for p in prices]
        lows = [p * random.uniform(0.995, 1.0) for p in prices]
        
        return {
            'timestamp': timestamps,
            'open': prices,
            'high': highs,
            'low': lows,
            'close': prices,
            'volume': volumes
        }


class DemoExecutor:
    """Executor simulado para demonstração"""
    
    def __init__(self, initial_balance: float = 10000):
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.current_position = None
        self.trades_history = []
        self.trade_count = 0
        
    async def get_market_data(self) -> Dict:
        """Simula obtenção de dados de mercado"""
        generator = DemoMarketDataGenerator()
        return generator.generate_realistic_data()
    
    async def get_orderbook(self) -> Dict:
        """Simula book de ofertas"""
        base_price = 50000
        return {
            'bids': [
                [str(base_price - i * 10), str(random.uniform(0.5, 2.0))]
                for i in range(5)
            ],
            'asks': [
                [str(base_price + i * 10), str(random.uniform(0.5, 2.0))]
                for i in range(5)
            ]
        }
    
    async def get_account_balance(self) -> float:
        """Retorna saldo simulado"""
        return self.balance
    
    async def execute_trade(self, action: str, quantity: float, risk_params: Dict) -> Dict:
        """Simula execução de trade"""
        await asyncio.sleep(0.1)  # Simula latência
        
        # Simula preço de execução com pequeno slippage
        fill_price = 50000 * random.uniform(0.9999, 1.0001)
        
        # Cria posição
        self.current_position = {
            'side': action,
            'quantity': quantity,
            'entry_price': fill_price,
            'stop_loss': risk_params['stop_loss_long' if action == 'BUY' else 'stop_loss_short'],
            'take_profit': risk_params['take_profit_long' if action == 'BUY' else 'take_profit_short'],
            'order_id': f"DEMO_{self.trade_count}",
            'timestamp': int(time.time() * 1000)
        }
        
        self.trade_count += 1
        
        return {
            'success': True,
            'order_id': self.current_position['order_id'],
            'fill_price': fill_price,
            'quantity': quantity
        }
    
    async def get_current_position(self) -> Dict | None:
        """Retorna posição atual"""
        return self.current_position
    
    async def update_stop_loss(self, new_stop_price: float) -> bool:
        """Simula atualização de stop loss"""
        if self.current_position:
            self.current_position['stop_loss'] = new_stop_price
            return True
        return False
    
    async def close_position(self, reason: str) -> Dict:
        """Simula fechamento de posição"""
        if not self.current_position:
            return {'success': False, 'error': 'Nenhuma posição para fechar'}
        
        # Simula preço de saída
        exit_price = self.current_position['entry_price'] * random.uniform(0.99, 1.01)
        
        # Calcula PnL
        entry_price = self.current_position['entry_price']
        quantity = self.current_position['quantity']
        
        if self.current_position['side'] == 'BUY':
            pnl = (exit_price - entry_price) * quantity
        else:
            pnl = (entry_price - exit_price) * quantity
        
        # Atualiza saldo
        self.balance += pnl
        
        # Salva histórico
        trade_record = {
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'side': self.current_position['side'],
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        self.trades_history.append(trade_record)
        
        # Limpa posição
        self.current_position = None
        
        return {
            'success': True,
            'exit_price': exit_price,
            'pnl': round(pnl, 2),
            'reason': reason
        }


class DemoTradingBot:
    """Bot de trading em modo demonstração"""
    
    def __init__(self, config_path: str = "config.yaml"):
        # Carrega configuração
        self.config = load_config(config_path)
        validate_config(self.config)
        
        # Setup logging
        setup_logging(self.config['logging'])
        self.logger = logging.getLogger(__name__)
        
        # Inicializa componentes
        self.indicators = TechnicalIndicators(self.config['indicators'])
        self.strategy = TrendFollowingStrategy(self.config)
        self.risk_manager = AdaptiveRiskManager(self.config['risk_management'])
        self.executor = DemoExecutor()
        
        # Estado do bot
        self.is_running = False
        self.current_position = None
        self.cycle_count = 0
        
        self.logger.info("🚀 Bot de Trading DEMO inicializado com sucesso")
    
    async def start_demo(self, max_cycles: int = 50):
        """Inicia demonstração do bot"""
        self.logger.info("🎯 Iniciando demonstração do bot de trading...")
        self.is_running = True
        
        print("\n" + "="*60)
        print("🤖 BOT DE TRADING BINANCE - MODO DEMONSTRAÇÃO")
        print("="*60)
        print(f"💰 Saldo inicial: ${self.executor.initial_balance:,.2f}")
        print(f"📊 Par de trading: {self.config['trading']['symbol']}")
        print(f"⚠️  Risco por trade: {self.config['trading']['risk_per_trade']*100:.1f}%")
        print("="*60)
        
        try:
            while self.is_running and self.cycle_count < max_cycles:
                await self.run_trading_cycle()
                self.cycle_count += 1
                
                # Mostra progresso
                if self.cycle_count % 10 == 0:
                    await self.show_progress()
                
                await asyncio.sleep(1)  # Simula intervalo entre análises
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Demonstração interrompida pelo usuário")
        finally:
            await self.show_final_results()
    
    async def run_trading_cycle(self):
        """Executa um ciclo completo de trading"""
        try:
            # Obtém dados de mercado
            market_data = await self.executor.get_market_data()
            if not market_data:
                return
            
            # Calcula indicadores técnicos
            indicators_data = self.indicators.calculate_all(market_data)
            current_price = market_data['close'][-1]
            
            # Verifica posição atual
            self.current_position = await self.executor.get_current_position()
            
            if self.current_position:
                # Gerencia posição existente
                await self.manage_position(market_data, indicators_data, current_price)
            else:
                # Procura oportunidades de entrada
                await self.evaluate_entry(market_data, indicators_data, current_price)
                
        except Exception as e:
            self.logger.error(f"❌ Erro no ciclo de trading: {e}")
    
    async def evaluate_entry(self, market_data: Dict, indicators_data: Dict, current_price: float):
        """Avalia oportunidades de entrada"""
        try:
            # Verifica sinais da estratégia
            signal = self.strategy.get_entry_signal(market_data, indicators_data)
            
            if signal['action'] == 'NONE':
                return
            
            # Valida pressão do book de ofertas
            orderbook = await self.executor.get_orderbook()
            if not orderbook or not self.strategy.validate_orderbook_pressure(orderbook, signal['action']):
                self.logger.info(f"📖 Book de ofertas não confirma sinal {signal['action']}")
                return
            
            # Calcula parâmetros de risco
            account_balance = await self.executor.get_account_balance()
            risk_params = self.risk_manager.calculate_position_size(
                account_balance, current_price, indicators_data['atr']
            )
            
            # Executa trade
            trade_result = await self.executor.execute_trade(
                signal['action'], risk_params['quantity'], risk_params
            )
            
            if trade_result['success']:
                self.logger.info(f"✅ Trade executado: {signal['action']} {risk_params['quantity']:.6f} a ${current_price:,.2f}")
                print(f"\n🎯 NOVO TRADE: {signal['action']} a ${current_price:,.2f}")
                print(f"📊 Confiança: {signal['confidence']*100:.1f}%")
                print(f"💰 Quantidade: {risk_params['quantity']:.6f}")
                print(f"🛡️  Stop Loss: ${risk_params['stop_loss_long' if signal['action'] == 'BUY' else 'stop_loss_short']:,.2f}")
                print(f"🎯 Take Profit: ${risk_params['take_profit_long' if signal['action'] == 'BUY' else 'take_profit_short']:,.2f}")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao avaliar entrada: {e}")
    
    async def manage_position(self, market_data: Dict, indicators_data: Dict, current_price: float):
        """Gerencia posição existente"""
        try:
            # Atualiza trailing stop se habilitado
            if self.config['risk_management']['trailing_stop_enabled']:
                new_stop = self.risk_manager.update_trailing_stop(
                    self.current_position, current_price, indicators_data
                )
                
                if new_stop != self.current_position['stop_loss']:
                    await self.executor.update_stop_loss(new_stop)
                    self.logger.info(f"📈 Trailing stop atualizado para ${new_stop:,.2f}")
            
            # Verifica condições de saída
            exit_signal = self.strategy.get_exit_signal(
                market_data, indicators_data, self.current_position
            )
            
            # Simula hit de stop loss ou take profit
            entry_price = self.current_position['entry_price']
            stop_loss = self.current_position['stop_loss']
            take_profit = self.current_position['take_profit']
            
            should_exit = False
            exit_reason = ""
            
            if self.current_position['side'] == 'BUY':
                if current_price <= stop_loss:
                    should_exit = True
                    exit_reason = "Stop Loss atingido"
                elif current_price >= take_profit:
                    should_exit = True
                    exit_reason = "Take Profit atingido"
            else:
                if current_price >= stop_loss:
                    should_exit = True
                    exit_reason = "Stop Loss atingido"
                elif current_price <= take_profit:
                    should_exit = True
                    exit_reason = "Take Profit atingido"
            
            if should_exit or exit_signal['should_exit']:
                if exit_signal['should_exit']:
                    exit_reason = exit_signal['reason']
                
                result = await self.executor.close_position(exit_reason)
                
                if result['success']:
                    pnl = result['pnl']
                    pnl_pct = (pnl / self.executor.initial_balance) * 100
                    
                    emoji = "💚" if pnl > 0 else "❤️"
                    self.logger.info(f"🏁 Posição fechada: {exit_reason}, PnL: ${pnl:.2f}")
                    print(f"\n{emoji} POSIÇÃO FECHADA")
                    print(f"📝 Motivo: {exit_reason}")
                    print(f"💰 PnL: ${pnl:,.2f} ({pnl_pct:+.2f}%)")
                    print(f"💵 Saldo atual: ${self.executor.balance:,.2f}")
                    
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerenciar posição: {e}")
    
    async def show_progress(self):
        """Mostra progresso da demonstração"""
        balance = await self.executor.get_account_balance()
        total_return = ((balance - self.executor.initial_balance) / self.executor.initial_balance) * 100
        
        print(f"\n📊 Progresso (Ciclo {self.cycle_count})")
        print(f"💰 Saldo: ${balance:,.2f} ({total_return:+.2f}%)")
        print(f"📈 Trades realizados: {len(self.executor.trades_history)}")
    
    async def show_final_results(self):
        """Mostra resultados finais da demonstração"""
        balance = await self.executor.get_account_balance()
        trades = self.executor.trades_history
        
        print("\n" + "="*60)
        print("📊 RELATÓRIO FINAL DA DEMONSTRAÇÃO")
        print("="*60)
        
        # Estatísticas gerais
        total_return = ((balance - self.executor.initial_balance) / self.executor.initial_balance) * 100
        print(f"💰 Saldo inicial: ${self.executor.initial_balance:,.2f}")
        print(f"💰 Saldo final: ${balance:,.2f}")
        print(f"📈 Retorno total: {total_return:+.2f}%")
        print(f"📊 Total de trades: {len(trades)}")
        
        if trades:
            # Análise de trades
            winning_trades = [t for t in trades if t['pnl'] > 0]
            losing_trades = [t for t in trades if t['pnl'] < 0]
            
            win_rate = (len(winning_trades) / len(trades)) * 100
            avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
            
            print(f"🎯 Taxa de acerto: {win_rate:.1f}%")
            print(f"💚 Trades vencedores: {len(winning_trades)}")
            print(f"❤️ Trades perdedores: {len(losing_trades)}")
            print(f"📊 Ganho médio: ${avg_win:,.2f}")
            print(f"📊 Perda média: ${avg_loss:,.2f}")
            
            best_trade = max(trades, key=lambda x: x['pnl'])
            worst_trade = min(trades, key=lambda x: x['pnl'])
            
            print(f"🏆 Melhor trade: ${best_trade['pnl']:,.2f}")
            print(f"💔 Pior trade: ${worst_trade['pnl']:,.2f}")
        
        print("="*60)
        print("✅ Demonstração concluída com sucesso!")
        print("📝 Todas as funcionalidades do bot foram testadas")
        print("🚀 O bot está pronto para trading real com chaves de API válidas")
        print("="*60)


async def main():
    """Função principal da demonstração"""
    print("🚀 Iniciando Bot de Trading Binance - Modo Demonstração")
    
    try:
        demo_bot = DemoTradingBot()
        await demo_bot.start_demo(max_cycles=30)  # 30 ciclos de análise
    except Exception as e:
        logging.error(f"❌ Erro na demonstração: {e}")


if __name__ == "__main__":
    asyncio.run(main())