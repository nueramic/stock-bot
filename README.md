# stock-bot

stock bot python

```mermaid

flowchart TD
    
    subgraph Запрос данных 
    
        stockRequest(SecurityRequest) --> |Асинхронные \n запросы к бирже| moex(((MOEX <br/>aiomoex)))
        stockRequest -.-> |Запросы в другие \n источники| anotherStockData(((STOCK DATA)))
        moex --> |парсинг| stockResponse(StockResponse)
        anotherStockData --> |возможно другой \nпарсинг| stockResponse(StockResponse)
    
    end 
    
    subgraph Инициализация процесса торговли 
    
        initialStretegies(Выбор пула стратегий и \n формирование правил торговли) --> dataRequirments(Требования к данным от биржи)
        dataRequirments --> stockRequest 
        style initialStretegies stroke-dasharray: 5 5
     
        
    end
    
    subgraph Стратегия 
        stockResponse --> |Передача данных в \n стратегию| strategy(Расчет стратегии и \n формирование ответа)
        strategy --> strategyResponse(StrategyResponse \n Требования к покупке \n или продаже)
    
    end
    
    subgraph Портфель 
        portfolio(Портфель. История торговли,\n статистики по портфелю)
        stockResponse --> |Передача данных на \n портфель| portfoliolog(Логирование данных в портфеле) 
        strategyResponse --> |Передача данных на \n портфель| portfoliocheck(Проверка на возможность \n совершения сделки)
        portfoliolog <-.-> portfolio
        portfoliocheck <-.-> portfolio
        
    end
    
    subgraph Покупка на бирже 
        portfolio --> stockPurchaseRequest(StockPurchaseRequest) 
        stockPurchaseRequest -.-> |Запрос на обновление данных \n если рассчет стратегии занял \nвремя большее тика| stockRequest 
        stockPurchaseRequest --> stockPurchaseResponse(StockPurchaseResponse)
        stockResponse --> |Передача данных на \n покупку| stockPurchaseResponse
        stockPurchaseResponse --> |Обновление состояния портфеля| portfolio
    
    end
        
```