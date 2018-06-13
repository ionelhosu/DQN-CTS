//
// Created by Mel Roderick on 8/11/17.
//

#ifndef CONTEXT_WEIGHTING_TREE_CTW_BYTE_H
#define CONTEXT_WEIGHTING_TREE_CTW_BYTE_H


#include <tiff.h>
#include "context_tree.h"
#include "cwt_node_symbol.h"

class cwt_symbol {
public:
    cwt_symbol(int context_depth, int alphabet_size);
    ~cwt_symbol();
    double update_and_logprob(uint8 *context, uint8 symbol) ;
    double logprob(uint8 *context, uint8 symbol) ;

    double m_log_alpha, m_log_1_minus_alpha;

private:
    cwt_node_symbol *m_root_node;
    int m_context_depth;
    int m_alphabet_size;

    int m_n;

    void check_input(uint8 *context, uint8 symbol);
};


#endif //CONTEXT_WEIGHTING_TREE_CTW_BYTE_H
