/*
* Copyright (C) Mellanox Technologies Ltd. 2017-2018.  ALL RIGHTS RESERVED.
*
* See file LICENSE for terms.
*/
#ifndef COMMON_DEFS_H_
#define COMMON_DEFS_H_

#ifndef __STDC_FORMAT_MACROS
    #define __STDC_FORMAT_MACROS 1
#endif

#include <inttypes.h>

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
# define BEGIN_C_DECLS  extern "C" {
# define END_C_DECLS    }
#else
# define BEGIN_C_DECLS
# define END_C_DECLS
#endif

#define CLX_DEFAULT_COLLECTOR_PORT      27500

#define CLX_PROVIDER_NAME_MAX           64

#define CLX_HOST_NAME_MAX               64

#define CLX_DATA_PATH_TEMPLATE          "{{year}}/{{month}}{{day}}/{{source}}/{{tag}}{{id}}.bin"

/* The i-th bit */
#define CLX_BIT(i)               (1ul << (i))

/* Mask of bits 0..i-1 */
#define CLX_MASK(i)              (CLX_BIT(i) - 1)

#define clx_likely(x)       __builtin_expect((x), 1)
#define clx_unlikely(x)     __builtin_expect((x), 0)

#define field_size(name, field) (sizeof(((struct name *)0)->field))

#define PRINT_FIELD_OFFSET(name, field) \
    printf(" %-25s  %-8lu  %-lu\n", #field, offsetof(name, field), field_size(name, field))

#define STATIC_ASSERT(COND, MSG) typedef char static_assertion_##MSG[(COND)?1:-1]

#define field_size(name, field) (sizeof(((struct name *)0)->field))

#define nof_array_elements(a) (sizeof(a) / sizeof(a[0]))

#define UNREFERENCED_PARAMETER(P) (P) = (P)

#endif  // COMMON_DEFS_H_
