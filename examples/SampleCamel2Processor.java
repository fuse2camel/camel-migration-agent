package com.example.processors;

import org.apache.camel.Exchange;
import org.apache.camel.Processor;

/**
 * Sample Camel 2 Processor that needs migration to Camel 4
 */
public class SampleCamel2Processor implements Processor {
    
    @Override
    public void process(Exchange exchange) throws Exception {
        // Camel 2 style - using getIn() and getOut()
        String inputBody = exchange.getIn().getBody(String.class);
        
        // Process the message
        String processedBody = processMessage(inputBody);
        
        // Set headers using getIn()
        exchange.getIn().setHeader("ProcessedBy", "SampleProcessor");
        exchange.getIn().setHeader("ProcessedAt", System.currentTimeMillis());
        
        // Set the output using getOut() - deprecated in Camel 4
        exchange.getOut().setBody(processedBody);
        exchange.getOut().setHeaders(exchange.getIn().getHeaders());
    }
    
    private String processMessage(String input) {
        if (input == null) {
            return "NO_DATA";
        }
        return "PROCESSED: " + input.toUpperCase();
    }
}
