## Процесс покупки на бирже

```mermaid

flowchart LR 
    
    %% Расположение узлов схемы 
    
    subgraph </b>
    
        StockPurchaseRequest(StockPurchaseRequest) 
        
        subgraph покупка 
            
            StockPurchaseProcess(StockPurchaseProcess)
            
        end 
        
        StockPurchaseResponse(StockPurchaseResponse)
    
    end 
    
    data(Данные об актуальных \n ценах и объемах)
    portfolioEnd(Portfolio)
    portfolioStart(Portfolio)
    
    %% Связи в схеме 
    
    portfolioStart --> StockPurchaseRequest
    
    StockPurchaseRequest --> StockPurchaseProcess
    
    StockPurchaseRequest --> data
    
    data --> StockPurchaseProcess
    
    StockPurchaseProcess --> StockPurchaseResponse
    
    StockPurchaseResponse --> portfolioEnd
    
   
```
